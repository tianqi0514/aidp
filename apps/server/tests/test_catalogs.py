from typing import Any

from fastapi.testclient import TestClient

from aidp.modules.catalogs.connectors import DiscoveredResource, connector_registry


class FakeConnector:
    def __init__(self) -> None:
        self.round = 0

    def test(self, config: dict[str, Any], secret: str | None) -> dict[str, Any]:
        assert config["database"] == "procurement"
        assert secret and "secret-password" in secret
        return {"latency_ms": 7, "database": "procurement", "server_version": "16"}

    def discover(
        self, config: dict[str, Any], secret: str | None, scope: dict[str, Any]
    ) -> list[DiscoveredResource]:
        self.round += 1
        purchase_fields = [
            {"name": "id", "type": "uuid", "nullable": False},
            {"name": "name", "type": "text", "nullable": False},
        ]
        if self.round > 1:
            purchase_fields.append({"name": "amount", "type": "numeric", "nullable": True})
        resources = [
            DiscoveredResource(
                external_id="procurement.public.purchase",
                name="purchase",
                namespace="public",
                category="table",
                schema={"fields": purchase_fields, "primary_key": ["id"]},
            )
        ]
        if self.round == 1:
            resources.append(
                DiscoveredResource(
                    external_id="procurement.public.supplier",
                    name="supplier",
                    namespace="public",
                    category="table",
                    schema={"fields": [], "primary_key": ["id"]},
                )
            )
        return resources


def _secret(client: TestClient, project_id: str) -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/secrets",
        json={
            "name": "postgres",
            "kind": "database_credentials",
            "value": '{"username":"aidp","password":"secret-password"}',
        },
    )
    return response.json()["id"]


def test_catalog_connection_and_safe_incremental_discovery(
    client: TestClient, project: dict, monkeypatch
):
    fake = FakeConnector()
    monkeypatch.setitem(connector_registry, "postgresql", fake)
    secret_id = _secret(client, project["id"])
    catalog = client.post(
        f"/api/v1/projects/{project['id']}/catalogs",
        json={
            "name": "business-db",
            "connector_type": "postgresql",
            "secret_id": secret_id,
            "config": {
                "host": "db.internal",
                "port": 5432,
                "database": "procurement",
                "schemas": ["public"],
            },
            "scope": "project",
            "read_only": True,
        },
    )
    assert catalog.status_code == 201
    catalog_id = catalog.json()["id"]

    tested = client.post(f"/api/v1/catalogs/{catalog_id}/test")
    assert tested.status_code == 200
    assert tested.json() == {
        "ok": True,
        "status": "healthy",
        "latency_ms": 7,
        "details": {"database": "procurement", "server_version": "16"},
        "error": None,
    }

    first = client.post(
        f"/api/v1/catalogs/{catalog_id}/discover-tasks",
        json={"strategy": "full_sync", "schemas": ["public"]},
    )
    assert first.status_code == 201
    assert first.json()["statistics"]["new"] == 2

    second = client.post(
        f"/api/v1/catalogs/{catalog_id}/discover-tasks",
        json={"strategy": "full_sync", "schemas": ["public"]},
    )
    assert second.status_code == 201
    assert second.json()["statistics"]["updated"] == 1
    assert second.json()["statistics"]["missing"] == 1

    resources = client.get(f"/api/v1/projects/{project['id']}/data-resources").json()
    assert {item["name"] for item in resources} == {"purchase", "supplier"}
    supplier = next(item for item in resources if item["name"] == "supplier")
    assert supplier["status"] == "stale"
    assert supplier["discovery_status"] == "missing"


def test_catalog_rejects_invalid_config_and_cross_project_secret(client: TestClient, project: dict):
    invalid = client.post(
        f"/api/v1/projects/{project['id']}/catalogs",
        json={
            "name": "invalid",
            "connector_type": "postgresql",
            "config": {"port": 5432},
            "read_only": True,
        },
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "CONNECTOR_CONFIG_INVALID"

    other = client.post(
        "/api/v1/projects",
        json={
            "name": "Other",
            "slug": "other-project",
            "description": "",
            "timezone": "Asia/Shanghai",
        },
    ).json()
    other_secret = _secret(client, other["id"])
    cross_project = client.post(
        f"/api/v1/projects/{project['id']}/catalogs",
        json={
            "name": "cross-project",
            "connector_type": "postgresql",
            "secret_id": other_secret,
            "config": {"host": "localhost", "database": "aidp"},
            "read_only": True,
        },
    )
    assert cross_project.status_code == 422
    assert cross_project.json()["code"] == "INVALID_SECRET_REFERENCE"
