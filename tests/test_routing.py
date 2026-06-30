"""Routing-logic tests for NotifySvc (NFR-2 / G-3: determinism)."""

from __future__ import annotations

from app.models import Route
from app.routing import bucket_of, channel_selected, route_channels


def _r(channel="email", **kw):
    return Route(event="order-shipped", channel=channel, **kw)


def test_disabled_route_never_selected():
    assert channel_selected(_r(enabled=False, sample_percent=100), "u1") is False


def test_full_sample_always_selected():
    assert channel_selected(_r(sample_percent=100), "anyone") is True


def test_zero_sample_never_selected():
    assert channel_selected(_r(sample_percent=0), "anyone") is False


def test_partial_sample_is_deterministic():
    route = _r(sample_percent=50)
    first = channel_selected(route, "user-42")
    for _ in range(50):
        assert channel_selected(route, "user-42") is first  # same inputs -> same answer


def test_bucket_is_stable_and_in_range():
    b = bucket_of("order-shipped", "email", "user-42")
    assert 0 <= b < 100
    assert b == bucket_of("order-shipped", "email", "user-42")  # reproducible


def test_partial_sample_approximates_percentage():
    route = _r(sample_percent=30)
    hits = sum(channel_selected(route, f"user-{i}") for i in range(2000))
    assert 0.24 < hits / 2000 < 0.36  # ~30% within tolerance


def test_route_channels_sorted_and_deduped():
    routes = [_r(channel="sms"), _r(channel="email"), _r(channel="email")]
    assert route_channels(routes, "u1") == ["email", "sms"]


def test_event_and_channel_change_bucket():
    # Including event+channel means the same recipient can differ across routes.
    a = bucket_of("order-shipped", "email", "u1")
    b = bucket_of("password-reset", "email", "u1")
    c = bucket_of("order-shipped", "sms", "u1")
    assert not (a == b == c)  # extremely unlikely to all collide
