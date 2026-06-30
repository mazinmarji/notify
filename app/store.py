"""In-memory route storage (BRD scope: in-memory, no DB)."""

from __future__ import annotations

from .models import Route


class DuplicateRouteError(KeyError):
    """Raised when creating a route whose (event, channel) exists (FR-1 -> 409)."""


class UnknownRouteError(KeyError):
    """Raised when a route is not found (FR-4/6 -> 404)."""


class RouteStore:
    """A tiny dict-backed store keyed by ``(event, channel)``.

    One instance per app; reset for tests.
    """

    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], Route] = {}

    def create(self, route: Route) -> Route:
        key = (route.event, route.channel)
        if key in self._routes:
            raise DuplicateRouteError(key)
        self._routes[key] = route
        return route

    def list(self) -> list[Route]:
        """All routes, in a stable order (event, then channel)."""
        return [self._routes[k] for k in sorted(self._routes)]

    def for_event(self, event: str) -> list[Route]:
        """Routes for ``event``, ordered by channel for determinism (FR-3)."""
        return [r for k, r in sorted(self._routes.items()) if k[0] == event]

    def get(self, event: str, channel: str) -> Route:
        try:
            return self._routes[(event, channel)]
        except KeyError as exc:
            raise UnknownRouteError((event, channel)) from exc

    def update(
        self, event: str, channel: str, *, enabled: bool | None, sample_percent: int | None
    ) -> Route:
        route = self.get(event, channel)
        updated = route.model_copy(
            update={
                k: v
                for k, v in (("enabled", enabled), ("sample_percent", sample_percent))
                if v is not None
            }
        )
        self._routes[(event, channel)] = updated
        return updated

    def delete(self, event: str, channel: str) -> None:
        try:
            del self._routes[(event, channel)]
        except KeyError as exc:
            raise UnknownRouteError((event, channel)) from exc

    def clear(self) -> None:
        self._routes.clear()
