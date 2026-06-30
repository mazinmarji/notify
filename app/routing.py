"""Deterministic notification routing.

NFR-2 / G-3: routing is pure and deterministic — no randomness, no clock. Which
channels a notification goes to depends only on ``(event, channel, recipient_id)``
and each route's ``sample_percent``, so the same inputs always yield the same
channels, and across many recipients the share routed to a partially-sampled
channel approximates its ``sample_percent``.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable

from .models import Route


def bucket_of(event: str, channel: str, recipient_id: str) -> int:
    """Map ``(event, channel, recipient_id)`` to a stable bucket in ``0..99``.

    Uses a SHA-256 digest of ``event:channel:recipient_id`` (not Python's salted
    ``hash()``, which varies per process) so the result is reproducible across
    runs and machines. Including ``event`` and ``channel`` means the same
    recipient can fall on different sides of the sample for different routes.
    """
    digest = hashlib.sha256(f"{event}:{channel}:{recipient_id}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 100


def channel_selected(route: Route, recipient_id: str) -> bool:
    """Whether ``route``'s channel fires for ``recipient_id`` (FR-5).

    - Disabled route -> always ``False``.
    - ``sample_percent >= 100`` -> always ``True``.
    - ``sample_percent <= 0`` -> always ``False``.
    - Partial sample -> deterministic per ``(event, channel, recipient_id)``.
    """
    if not route.enabled:
        return False
    if route.sample_percent >= 100:
        return True
    if route.sample_percent <= 0:
        return False
    return bucket_of(route.event, route.channel, recipient_id) < route.sample_percent


def route_channels(routes: Iterable[Route], recipient_id: str) -> list[str]:
    """The sorted, de-duplicated channels a notification routes to (FR-5).

    Deterministic: the result depends only on the routes and ``recipient_id``.
    """
    selected = {r.channel for r in routes if channel_selected(r, recipient_id)}
    return sorted(selected)
