from fastapi.testclient import TestClient


def test_full_business_model_validation_and_publish(client: TestClient, project: dict):
    network = client.post(
        f"/api/v1/projects/{project['id']}/knowledge-networks",
        json={
            "key": "procurement",
            "name": "采购知识网络",
            "description": "采购对象、关系与行动",
            "branch": "main",
            "concept_groups": [{"key": "transactions", "name": "交易对象"}],
        },
    )
    assert network.status_code == 201
    network_id = network.json()["id"]

    def create_object(key: str, name: str):
        response = client.post(
            f"/api/v1/knowledge-networks/{network_id}/object-types",
            json={
                "key": key,
                "name": name,
                "properties": [
                    {
                        "key": "id",
                        "name": "ID",
                        "data_type": "string",
                        "nullable": False,
                    },
                    {
                        "key": "name",
                        "name": "名称",
                        "data_type": "string",
                        "nullable": False,
                    },
                ],
                "primary_keys": ["id"],
                "display_key": "name",
                "indexes": [{"type": "keyword", "properties": ["id"]}],
            },
        )
        assert response.status_code == 201
        return response.json()

    purchase = create_object("purchase", "采购项目")
    supplier = create_object("supplier", "供应商")

    relation = client.post(
        f"/api/v1/knowledge-networks/{network_id}/relation-types",
        json={
            "key": "purchase_supplier",
            "name": "采购供应商",
            "source_object_type_id": purchase["id"],
            "target_object_type_id": supplier["id"],
            "cardinality": "many_to_many",
            "mapping_type": "direct",
            "mapping": {"field_pairs": [{"source": "supplier_id", "target": "id"}]},
            "properties": [],
        },
    )
    assert relation.status_code == 201

    action = client.post(
        f"/api/v1/knowledge-networks/{network_id}/action-types",
        json={
            "key": "create_remediation",
            "name": "创建整改任务",
            "operation": "modify",
            "object_type_id": purchase["id"],
            "condition": {"status": "non_compliant"},
            "impact_contract": {"operation": "modify", "fields": ["status"]},
            "parameters_schema": {"type": "object", "properties": {}},
            "executor": {"type": "mcp", "id": "create_task"},
            "permission": "ask",
            "retry_policy": {"max_attempts": 2},
            "compensation": {},
        },
    )
    assert action.status_code == 201

    validation = client.post(f"/api/v1/knowledge-networks/{network_id}/validate")
    assert validation.status_code == 200
    assert validation.json()["valid"] is True
    assert validation.json()["summary"] == {
        "objects": 2,
        "relations": 1,
        "actions": 1,
        "errors": 0,
        "warnings": 0,
    }

    published = client.post(f"/api/v1/knowledge-networks/{network_id}/publish")
    assert published.status_code == 200
    assert published.json()["status"] == "published"

    immutable = client.post(
        f"/api/v1/knowledge-networks/{network_id}/object-types",
        json={
            "key": "approval",
            "name": "审批",
            "properties": [{"key": "id", "name": "ID", "data_type": "string"}],
            "primary_keys": ["id"],
        },
    )
    assert immutable.status_code == 409
