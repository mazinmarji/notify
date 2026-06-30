from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_store
from app.store import RouteStore


@pytest.fixture()
def store() -> RouteStore:
    return RouteStore()


@pytest.fixture()
def client(store: RouteStore) -> TestClient:
    app.dependency_overrides[get_store] = lambda: store
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
