from fastapi.testclient import TestClient

from aidp.core.config import Settings


def test_comma_separated_cors_configuration(monkeypatch):
    monkeypatch.setenv("AIDP_CORS_ORIGINS", "http://localhost:5173,http://localhost:8080")
    assert Settings().cors_origins == ["http://localhost:5173", "http://localhost:8080"]


def test_health_and_project_lifecycle(client: TestClient):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.headers["x-request-id"]

    payload = {
        "name": "Operations",
        "slug": "operations",
        "description": "Operations project",
        "timezone": "Asia/Shanghai",
    }
    created = client.post("/api/v1/projects", json=payload)
    assert created.status_code == 201
    project_id = created.json()["id"]

    duplicate = client.post("/api/v1/projects", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "RESOURCE_CONFLICT"

    updated = client.patch(f"/api/v1/projects/{project_id}", json={"description": "Updated"})
    assert updated.status_code == 200
    assert updated.json()["description"] == "Updated"


def test_user_membership_and_secret_never_reveals_value(client: TestClient, project: dict):
    user = client.post(
        "/api/v1/users",
        json={"email": "owner@example.com", "display_name": "Owner"},
    )
    assert user.status_code == 201

    member = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"user_id": user.json()["id"], "role": "admin"},
    )
    assert member.status_code == 201
    assert member.json()["role"] == "admin"

    raw_value = '{"username":"aidp","password":"secret-password"}'
    secret = client.post(
        f"/api/v1/projects/{project['id']}/secrets",
        json={"name": "postgres", "kind": "database_credentials", "value": raw_value},
    )
    assert secret.status_code == 201
    assert "value" not in secret.json()
    assert "password" not in secret.text

    listed = client.get(f"/api/v1/projects/{project['id']}/secrets")
    assert listed.status_code == 200
    assert listed.json()[0]["name"] == "postgres"
    assert raw_value not in listed.text
