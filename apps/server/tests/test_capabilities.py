from fastapi.testclient import TestClient

from aidp.modules.capabilities.models import CapabilityInvocation


def test_capability_catalog_preview_confirmation_and_audit(client: TestClient, db):
    response = client.get("/api/v1/agent/capabilities")
    assert response.status_code == 200
    capabilities = {item["name"]: item for item in response.json()}
    assert "projects.create" in capabilities
    assert "catalogs.discover" in capabilities
    assert "knowledge_networks.publish" in capabilities
    assert capabilities["knowledge_networks.publish"]["risk"] == "high"

    payload = {
        "name": "Agent-created project",
        "slug": "agent-created",
        "description": "Created through the same application service",
        "timezone": "Asia/Shanghai",
    }
    preview = client.post(
        "/api/v1/agent/capabilities/projects.create:invoke",
        json={"input": payload, "mode": "preview"},
    )
    assert preview.status_code == 200
    assert preview.json()["status"] == "validated"
    assert preview.json()["requires_confirmation"] is True
    assert client.get("/api/v1/projects").json() == []

    rejected = client.post(
        "/api/v1/agent/capabilities/projects.create:invoke",
        json={"input": payload, "mode": "execute", "confirmed": False},
    )
    assert rejected.status_code == 409
    assert rejected.json()["code"] == "CAPABILITY_CONFIRMATION_REQUIRED"

    executed = client.post(
        "/api/v1/agent/capabilities/projects.create:invoke",
        json={
            "input": payload,
            "mode": "execute",
            "confirmed": True,
            "actor_id": "test-agent",
        },
    )
    assert executed.status_code == 200
    assert executed.json()["status"] == "completed"
    assert executed.json()["output"]["slug"] == "agent-created"

    invocation_id = executed.json()["invocation_id"]
    invocation = db.get(CapabilityInvocation, invocation_id)
    assert invocation is not None
    assert invocation.actor_id == "test-agent"
    assert invocation.status == "completed"


def test_agent_can_validate_a_multi_step_plan_before_execution(client: TestClient):
    plan = client.post(
        "/api/v1/agent/capabilities/validate-plan",
        json={
            "steps": [
                {
                    "id": "create-project",
                    "capability": "projects.create",
                    "input": {
                        "name": "Plan project",
                        "slug": "plan-project",
                        "description": "",
                        "timezone": "Asia/Shanghai",
                    },
                    "confirmed": False,
                },
                {
                    "id": "unknown",
                    "capability": "missing.capability",
                    "input": {},
                },
            ]
        },
    )
    assert plan.status_code == 200
    assert plan.json()["valid"] is False
    assert "confirmation" in plan.json()["steps"][0]["errors"][0]
    assert plan.json()["steps"][1]["valid"] is False
