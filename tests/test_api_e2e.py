"""End-to-end API smoke test through the real ASGI app (SQLite temp DB).

Exercises the master-data → production slice over HTTP and checks the audit
trail recorded the actions. Uses FastAPI's TestClient so the lifespan (table
creation + subscriber install) runs.
"""

from __future__ import annotations

import os
import tempfile

import pytest


@pytest.fixture
def client():
    # Point the app at an isolated temp SQLite file before anything is cached.
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["MES_DATABASE_URL"] = f"sqlite+aiosqlite:///{path}"
    os.environ["MES_ENVIRONMENT"] = "dev"

    from mes_core import config
    from mes_core.shared import db

    config.get_settings.cache_clear()
    db.get_engine.cache_clear()
    db.session_factory.cache_clear()

    from fastapi.testclient import TestClient

    from mes_core.main import create_app

    with TestClient(create_app()) as c:
        yield c

    try:
        os.remove(path)
    except OSError:
        pass


def test_master_data_to_production_flow(client):
    assert client.get("/health").json()["status"] == "ok"

    material = client.post(
        "/master-data/materials", json={"code": "MAT-1", "name": "Bottle"}
    ).json()
    product = client.post(
        "/master-data/products",
        json={"code": "PRD-1", "name": "Bottled Water", "material_id": material["id"]},
    ).json()
    route = client.post(
        "/master-data/routes",
        json={
            "product_id": product["id"],
            "version": 1,
            "steps": [{"name": "Fill"}, {"name": "Cap"}],
        },
    ).json()
    client.post(f"/master-data/routes/{route['id']}/approve")

    order = client.post(
        "/production/orders",
        json={
            "order_no": "WO-1",
            "product_id": product["id"],
            "route_id": route["id"],
            "quantity": 100,
        },
    ).json()
    assert order["state"] == "created"

    released = client.post(f"/production/orders/{order['id']}/release").json()
    assert released["state"] == "released"

    # Audit trail recorded the actions and the hash chain is intact.
    audit = client.get("/compliance/audit").json()
    actions = {row["action"] for row in audit}
    assert {"create", "approve", "release"} <= actions
    assert client.get("/compliance/audit/verify").json()["intact"] is True
