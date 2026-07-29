from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aidp.core.errors import ConflictError, DomainError, NotFoundError
from aidp.modules.catalogs.models import DataResource
from aidp.modules.knowledge_networks.models import (
    ActionType,
    KnowledgeNetwork,
    ObjectType,
    RelationType,
)
from aidp.modules.knowledge_networks.schemas import (
    ActionTypeCreate,
    KnowledgeNetworkCreate,
    ObjectTypeCreate,
    RelationTypeCreate,
)
from aidp.modules.projects.service import ProjectService


class KnowledgeNetworkService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, project_id: str, data: KnowledgeNetworkCreate) -> KnowledgeNetwork:
        ProjectService(self.session).get(project_id)
        network = KnowledgeNetwork(project_id=project_id, **data.model_dump())
        self.session.add(network)
        self._commit_unique("A knowledge network with this key and version already exists")
        self.session.refresh(network)
        return network

    def list(self, project_id: str) -> list[KnowledgeNetwork]:
        return list(
            self.session.scalars(
                select(KnowledgeNetwork)
                .where(KnowledgeNetwork.project_id == project_id)
                .order_by(KnowledgeNetwork.key, KnowledgeNetwork.version.desc())
            )
        )

    def get(self, network_id: str) -> KnowledgeNetwork:
        network = self.session.get(KnowledgeNetwork, network_id)
        if network is None:
            raise NotFoundError("KnowledgeNetwork", network_id)
        return network

    def _ensure_draft(self, network_id: str) -> KnowledgeNetwork:
        network = self.get(network_id)
        if network.status != "draft":
            raise ConflictError("Published knowledge network versions are immutable")
        return network

    def create_object_type(self, network_id: str, data: ObjectTypeCreate) -> ObjectType:
        network = self._ensure_draft(network_id)
        if data.source_resource_id:
            resource = self.session.get(DataResource, data.source_resource_id)
            if resource is None or resource.project_id != network.project_id:
                raise DomainError(
                    "INVALID_SOURCE_RESOURCE", "Source resource does not belong to this project"
                )
        item = ObjectType(
            network_id=network_id,
            **data.model_dump(mode="json"),
        )
        self.session.add(item)
        self._commit_unique("An object type with this key already exists in the network")
        self.session.refresh(item)
        return item

    def list_object_types(self, network_id: str) -> list[ObjectType]:
        self.get(network_id)
        return list(
            self.session.scalars(
                select(ObjectType)
                .where(ObjectType.network_id == network_id)
                .order_by(ObjectType.name)
            )
        )

    def _object_in_network(self, network_id: str, object_id: str) -> ObjectType:
        item = self.session.get(ObjectType, object_id)
        if item is None or item.network_id != network_id:
            raise DomainError("INVALID_OBJECT_TYPE", "Object type does not belong to this network")
        return item

    def create_relation_type(self, network_id: str, data: RelationTypeCreate) -> RelationType:
        self._ensure_draft(network_id)
        self._object_in_network(network_id, data.source_object_type_id)
        self._object_in_network(network_id, data.target_object_type_id)
        item = RelationType(network_id=network_id, **data.model_dump(mode="json"))
        self.session.add(item)
        self._commit_unique("A relation type with this key already exists in the network")
        self.session.refresh(item)
        return item

    def list_relation_types(self, network_id: str) -> list[RelationType]:
        self.get(network_id)
        return list(
            self.session.scalars(
                select(RelationType)
                .where(RelationType.network_id == network_id)
                .order_by(RelationType.name)
            )
        )

    def create_action_type(self, network_id: str, data: ActionTypeCreate) -> ActionType:
        self._ensure_draft(network_id)
        self._object_in_network(network_id, data.object_type_id)
        item = ActionType(network_id=network_id, **data.model_dump(mode="json"))
        self.session.add(item)
        self._commit_unique("An action type with this key already exists in the network")
        self.session.refresh(item)
        return item

    def list_action_types(self, network_id: str) -> list[ActionType]:
        self.get(network_id)
        return list(
            self.session.scalars(
                select(ActionType)
                .where(ActionType.network_id == network_id)
                .order_by(ActionType.name)
            )
        )

    def validate(self, network_id: str) -> dict:
        network = self.get(network_id)
        objects = self.list_object_types(network_id)
        relations = self.list_relation_types(network_id)
        actions = self.list_action_types(network_id)
        issues: list[dict] = []
        if not objects:
            issues.append(
                {
                    "level": "error",
                    "code": "NO_OBJECT_TYPES",
                    "message": "The knowledge network must contain at least one object type",
                    "resource_type": "knowledge_network",
                    "resource_id": network.id,
                }
            )
        object_ids = {item.id for item in objects}
        for item in objects:
            property_keys = {prop["key"] for prop in item.properties}
            missing = set(item.primary_keys) - property_keys
            if missing:
                issues.append(
                    {
                        "level": "error",
                        "code": "INVALID_PRIMARY_KEY",
                        "message": f"Primary keys not found in properties: {sorted(missing)}",
                        "resource_type": "object_type",
                        "resource_id": item.id,
                    }
                )
        for relation in relations:
            if (
                relation.source_object_type_id not in object_ids
                or relation.target_object_type_id not in object_ids
            ):
                issues.append(
                    {
                        "level": "error",
                        "code": "INVALID_RELATION_ENDPOINT",
                        "message": "Relation endpoint is missing from this network",
                        "resource_type": "relation_type",
                        "resource_id": relation.id,
                    }
                )
            if relation.mapping_type == "direct" and not relation.mapping.get("field_pairs"):
                issues.append(
                    {
                        "level": "error",
                        "code": "EMPTY_RELATION_MAPPING",
                        "message": "Direct relation requires at least one field pair",
                        "resource_type": "relation_type",
                        "resource_id": relation.id,
                    }
                )
        for action in actions:
            if action.object_type_id not in object_ids:
                issues.append(
                    {
                        "level": "error",
                        "code": "INVALID_ACTION_OBJECT",
                        "message": "Action target object is missing from this network",
                        "resource_type": "action_type",
                        "resource_id": action.id,
                    }
                )
            if not action.executor.get("type") or not action.executor.get("id"):
                issues.append(
                    {
                        "level": "error",
                        "code": "INVALID_ACTION_EXECUTOR",
                        "message": "Action executor requires type and id",
                        "resource_type": "action_type",
                        "resource_id": action.id,
                    }
                )
            if action.permission == "allow" and action.operation != "add":
                issues.append(
                    {
                        "level": "warning",
                        "code": "ACTION_WITHOUT_CONFIRMATION",
                        "message": "Modify/delete actions should normally require confirmation",
                        "resource_type": "action_type",
                        "resource_id": action.id,
                    }
                )
        errors = sum(issue["level"] == "error" for issue in issues)
        warnings = len(issues) - errors
        return {
            "valid": errors == 0,
            "issues": issues,
            "summary": {
                "objects": len(objects),
                "relations": len(relations),
                "actions": len(actions),
                "errors": errors,
                "warnings": warnings,
            },
        }

    def publish(self, network_id: str) -> KnowledgeNetwork:
        network = self._ensure_draft(network_id)
        result = self.validate(network_id)
        if not result["valid"]:
            raise DomainError(
                "NETWORK_VALIDATION_FAILED",
                f"Knowledge network has {result['summary']['errors']} validation errors",
                422,
            )
        network.status = "published"
        self.session.commit()
        self.session.refresh(network)
        return network

    def _commit_unique(self, message: str) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError(message) from exc
