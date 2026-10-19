def test_add_and_list_comments(client, make_ticket):
    ticket = make_ticket()
    url = f"/tickets/{ticket['id']}/comments"

    client.post(url, json={"author": "zara", "body": "Can you restart the laptop?"})
    client.post(url, json={"author": "zara", "body": "User is VIP", "internal": True})

    everything = client.get(url).json()
    assert [c["body"] for c in everything] == ["Can you restart the laptop?", "User is VIP"]

    public = client.get(url, params={"include_internal": False}).json()
    assert [c["body"] for c in public] == ["Can you restart the laptop?"]


def test_comment_on_unknown_ticket_returns_404(client):
    response = client.post("/tickets/42/comments", json={"author": "zara", "body": "Hello"})
    assert response.status_code == 404


def test_comments_are_deleted_with_ticket(client, make_ticket):
    ticket = make_ticket()
    client.post(f"/tickets/{ticket['id']}/comments", json={"author": "zara", "body": "Note"})
    client.delete(f"/tickets/{ticket['id']}")
    assert client.get(f"/tickets/{ticket['id']}/comments").status_code == 404
