from datetime import UTC, datetime, timedelta

from app.models import Ticket


def test_stats_on_empty_database(client):
    stats = client.get("/stats").json()
    assert stats["total"] == 0
    assert stats["overdue"] == 0
    assert stats["avg_resolution_hours"] is None


def test_stats(client, db, make_ticket):
    a = make_ticket(priority="high")
    b = make_ticket(priority="low")
    make_ticket(priority="low")

    client.patch(f"/tickets/{a['id']}", json={"status": "resolved"})
    resolved = db.get(Ticket, a["id"])
    resolved.resolved_at = resolved.created_at + timedelta(hours=3)
    db.get(Ticket, b["id"]).due_at = datetime.now(UTC) - timedelta(minutes=5)
    db.commit()

    stats = client.get("/stats").json()
    assert stats["total"] == 3
    assert stats["by_status"] == {"open": 2, "in_progress": 0, "resolved": 1, "closed": 0}
    assert stats["by_priority"]["low"] == 2
    assert stats["overdue"] == 1
    assert stats["avg_resolution_hours"] == 3.0
