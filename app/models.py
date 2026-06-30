"""Request/response models for NotifySvc (data model: section 5 of the BRD)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

NAME_PATTERN = r"^[a-z0-9-]+$"


class Route(BaseModel):
    """A routing rule: ``Route { event, channel, enabled, sample_percent }``.

    Maps an ``event`` type to a delivery ``channel``. ``sample_percent`` allows a
    deterministic partial rollout of a channel (e.g. send 10% of ``order-shipped``
    events to ``sms``), resolved per recipient — never randomly (G-3).
    """

    model_config = ConfigDict(extra="forbid")

    event: str = Field(pattern=NAME_PATTERN)
    channel: str = Field(pattern=NAME_PATTERN)
    enabled: bool = True
    sample_percent: int = Field(default=100, ge=0, le=100)


class RouteUpdate(BaseModel):
    """Partial update for PATCH /routes/{event}/{channel} (FR-4)."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool | None = None
    sample_percent: int | None = Field(default=None, ge=0, le=100)


class RouteDecision(BaseModel):
    """Result of POST /route (FR-5): the channels a notification routes to."""

    event: str
    recipient_id: str
    channels: list[str]
