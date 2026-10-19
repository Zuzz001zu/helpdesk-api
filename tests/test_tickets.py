from datetime import UTC, datetime, timedelta

from app.models import Ticket


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_ticket_sets_sla(make_ticket):
    ticket = make_ticket(priority="critical")

    created = datetime.fromisoformat(ticket["created_at"])
    due = datetime.fromisoformat(ticket["due_at"])
    assert ticket["status"] == "open"
    assert due - created == timedelta(hours=4)
    assert ticket["overdue"] is False


def test_create_ticket_validates_input(client):
    response = client.post("/tickets", json={"title": "x", "requester_email": "not-an-email"})
    assert response.status_code == 422


def test_write_requires_api_key(client):
    response = client.post(
        "/tickets",
        json={"title": "Printer jam", "requester_email": "a@example.com"},
        headers={"X-API-Key": "wrong"},
    )
    assert response.status_code == 401


def test_read_does_not_require_api_key(client, make_ticket):
    ticket = make_ticket()
    response = client.get(f"/tickets/{ticket['id']}", headers={"X-API-Key": ""})
    assert response.status_code == 200


def test_get_unknown_ticket_returns_404(client):
    assert client.get("/tickets/999").status_code == 404


def test_list_filters_and_search(client, make_ticket):
    make_ticket(title="Outlook asks for password", priority="low")
    make_ticket(title="Laptop screen broken", priority="high")
    make_ticket(title="Outlook calendar not syncing", priority="high")

    high = client.get("/tickets", params={"priority": "high"}).json()
    assert high["total"] == 2

    outlook = client.get("/tickets", params={"q": "outlook"}).json()
    assert {t["title"] for t in outlook["items"]} == {
        "Outlook asks for password",
        "Outlook calendar not syncing",
    }


def test_list_is_paginated_and_sorted_by_due_date(client, make_ticket):
    for priority in ["low", "critical", "medium"]:
        make_ticket(priority=priority)

    page = client.get("/tickets", params={"limit": 2}).json()
    assert page["total"] == 3
    assert [t["priority"] for t in page["items"]] == ["critical", "medium"]

    rest = client.get("/tickets", params={"limit": 2, "offset": 2}).json()
    assert [t["priority"] for t in rest["items"]] == ["low"]


def test_overdue_filter(client, db, make_ticket):
    late = make_ticket(title="Old request")
    make_ticket(title="New request")
    db.get(Ticket, late["id"]).due_at = datetime.now(UTC) - timedelta(hours=1)
    db.commit()

    overdue = client.get("/tickets", params={"overdue": True}).json()
    assert [t["title"] for t in overdue["items"]] == ["Old request"]
    assert overdue["items"][0]["overdue"] is True


def test_status_workflow(client, make_ticket):
    ticket = make_ticket()
    url = f"/tickets/{ticket['id']}"

    in_progress = client.patch(url, json={"status": "in_progress", "assignee": "zara"}).json()
    assert in_progress["assignee"] == "zara"

    resolved = client.patch(url, json={"status": "resolved"}).json()
    assert resolved["resolved_at"] is not None

    reopened = client.patch(url, json={"status": "open"}).json()
    assert reopened["resolved_at"] is None


def test_invalid_transition_returns_409(client, make_ticket):
    ticket = make_ticket()
    response = client.patch(f"/tickets/{ticket['id']}", json={"status": "closed"})
    assert response.status_code == 409
    assert "Cannot move ticket" in response.json()["detail"]


def test_priority_change_recalculates_due_date(client, make_ticket):
    ticket = make_ticket(priority="low")
    updated = client.patch(f"/tickets/{ticket['id']}", json={"priority": "critical"}).json()

    created = datetime.fromisoformat(updated["created_at"])
    assert datetime.fromisoformat(updated["due_at"]) - created == timedelta(hours=4)


def test_delete_ticket(client, make_ticket):
    ticket = make_ticket()
    assert client.delete(f"/tickets/{ticket['id']}").status_code == 204
    assert client.get(f"/tickets/{ticket['id']}").status_code == 404
