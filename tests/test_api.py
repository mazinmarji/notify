"""API tests for NotifySvc (FR-1..FR-7, NFR-1)."""

from __future__ import annotations


def _route(event="order-shipped", channel="email", **kw):
    return {"event": event, "channel": channel, **kw}


def test_health(client):  # FR-7
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_and_get_event_routes(client):  # FR-1, FR-3
    assert client.post("/routes", json=_route(channel="email")).status_code == 201
    assert client.post("/routes", json=_route(channel="sms")).status_code == 201
    r = client.get("/routes/order-shipped")
    assert r.status_code == 200
    channels = [x["channel"] for x in r.json()]
    assert channels == ["email", "sms"]  # ordered by channel


def test_create_duplicate_conflicts(client):  # FR-1 -> 409
    assert client.post("/routes", json=_route()).status_code == 201
    r = client.post("/routes", json=_route())
    assert r.status_code == 409


def test_list_routes_stable_order(client):  # FR-2
    client.post("/routes", json=_route(event="b-event", channel="sms"))
    client.post("/routes", json=_route(event="a-event", channel="push"))
    keys = [(x["event"], x["channel"]) for x in client.get("/routes").json()]
    assert keys == [("a-event", "push"), ("b-event", "sms")]


def test_update_route(client):  # FR-4
    client.post("/routes", json=_route())
    r = client.patch("/routes/order-shipped/email", json={"sample_percent": 50, "enabled": False})
    assert r.status_code == 200
    body = r.json()
    assert body["sample_percent"] == 50 and body["enabled"] is False


def test_update_unknown_route_404(client):  # FR-4 -> 404
    assert client.patch("/routes/nope/email", json={"enabled": False}).status_code == 404


def test_delete_route(client):  # FR-6
    client.post("/routes", json=_route())
    assert client.delete("/routes/order-shipped/email").status_code == 204
    assert client.get("/routes/order-shipped").json() == []


def test_delete_unknown_route_404(client):  # FR-6 -> 404
    assert client.delete("/routes/nope/email").status_code == 404


def test_invalid_sample_percent_422(client):  # NFR-1
    assert client.post("/routes", json=_route(sample_percent=150)).status_code == 422


def test_invalid_name_pattern_422(client):  # NFR-1
    assert client.post("/routes", json=_route(event="Order Shipped")).status_code == 422


def test_route_notification_full_channels(client):  # FR-5
    client.post("/routes", json=_route(channel="email"))
    client.post("/routes", json=_route(channel="push"))
    r = client.post("/route", json={"event": "order-shipped", "recipient_id": "u1"})
    assert r.status_code == 200
    assert r.json()["channels"] == ["email", "push"]


def test_route_notification_skips_disabled(client):  # FR-5
    client.post("/routes", json=_route(channel="email"))
    client.post("/routes", json=_route(channel="sms", enabled=False))
    body = client.post("/route", json={"event": "order-shipped", "recipient_id": "u1"}).json()
    assert body["channels"] == ["email"]
