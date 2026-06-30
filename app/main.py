"""NotifySvc HTTP API (FR-1..FR-7).

A self-contained notification-routing service: register routes that map an event
to a delivery channel (with optional deterministic percentage sampling), then
resolve which channels a notification for a recipient goes to. No persistence,
auth, or network calls (BRD scope + NFR-3).
"""

from __future__ import annotations

from fastapi import Body, Depends, FastAPI, HTTPException, Response

from .models import Route, RouteDecision, RouteUpdate
from .routing import route_channels
from .store import DuplicateRouteError, RouteStore, UnknownRouteError

app = FastAPI(title="NotifySvc", version="0.1.0")

# Single process-wide store. Exposed via a dependency so tests can override it.
_store = RouteStore()


def get_store() -> RouteStore:
    return _store


@app.get("/health")
def health() -> dict[str, str]:
    """FR-7: liveness probe."""
    return {"status": "ok"}


@app.post("/routes", status_code=201, response_model=Route)
def create_route(route: Route, store: RouteStore = Depends(get_store)) -> Route:
    """FR-1: create a route; duplicate (event, channel) -> 409."""
    try:
        return store.create(route)
    except DuplicateRouteError:
        raise HTTPException(
            status_code=409,
            detail=f"route '{route.event}->{route.channel}' already exists",
        )


@app.get("/routes", response_model=list[Route])
def list_routes(store: RouteStore = Depends(get_store)) -> list[Route]:
    """FR-2: list all routes."""
    return store.list()


@app.get("/routes/{event}", response_model=list[Route])
def get_event_routes(event: str, store: RouteStore = Depends(get_store)) -> list[Route]:
    """FR-3: list routes for one event (ordered by channel)."""
    return store.for_event(event)


@app.patch("/routes/{event}/{channel}", response_model=Route)
def update_route(
    event: str,
    channel: str,
    update: RouteUpdate,
    store: RouteStore = Depends(get_store),
) -> Route:
    """FR-4: partially update a route; unknown -> 404."""
    try:
        return store.update(
            event, channel, enabled=update.enabled, sample_percent=update.sample_percent
        )
    except UnknownRouteError:
        raise HTTPException(
            status_code=404, detail=f"route '{event}->{channel}' not found"
        )


@app.post("/route", response_model=RouteDecision)
def route_notification(
    event: str = Body(..., embed=True),
    recipient_id: str = Body(..., embed=True),
    store: RouteStore = Depends(get_store),
) -> RouteDecision:
    """FR-5: deterministically resolve the channels for a notification."""
    channels = route_channels(store.for_event(event), recipient_id)
    return RouteDecision(event=event, recipient_id=recipient_id, channels=channels)


@app.delete("/routes/{event}/{channel}", status_code=204)
def delete_route(
    event: str, channel: str, store: RouteStore = Depends(get_store)
) -> Response:
    """FR-6: delete a route; unknown -> 404."""
    try:
        store.delete(event, channel)
    except UnknownRouteError:
        raise HTTPException(
            status_code=404, detail=f"route '{event}->{channel}' not found"
        )
    return Response(status_code=204)
