from typing import Any

from aidp.core.schemas import APIModel
from aidp.modules.capabilities.registry import Capability, registry
from aidp.modules.catalogs.schemas import (
    CatalogCreate,
    CatalogResponse,
    ConnectionTestResponse,
    DiscoveryRequest,
    DiscoveryRunResponse,
)
from aidp.modules.catalogs.service import CatalogService
from aidp.modules.knowledge_networks.schemas import (
    ActionTypeCreate,
    ActionTypeResponse,
    KnowledgeNetworkCreate,
    KnowledgeNetworkResponse,
    NetworkValidationResponse,
    ObjectTypeCreate,
    ObjectTypeResponse,
    RelationTypeCreate,
    RelationTypeResponse,
)
from aidp.modules.knowledge_networks.service import KnowledgeNetworkService
from aidp.modules.projects.schemas import ProjectCreate, ProjectResponse
from aidp.modules.projects.service import ProjectService


class EmptyInput(APIModel):
    pass


class ProjectCreateInput(ProjectCreate):
    pass


class CatalogCreateInput(CatalogCreate):
    project_id: str


class CatalogIdInput(APIModel):
    catalog_id: str


class CatalogDiscoveryInput(DiscoveryRequest):
    catalog_id: str


class KnowledgeNetworkCreateInput(KnowledgeNetworkCreate):
    project_id: str


class ObjectTypeCreateInput(ObjectTypeCreate):
    network_id: str


class RelationTypeCreateInput(RelationTypeCreate):
    network_id: str


class ActionTypeCreateInput(ActionTypeCreate):
    network_id: str


class NetworkIdInput(APIModel):
    network_id: str


def _without(model: APIModel, *fields: str) -> dict[str, Any]:
    return model.model_dump(exclude=set(fields))


def register_builtin_capabilities() -> None:
    if registry.list():
        return
    registry.register(
        Capability(
            name="projects.create",
            module="projects",
            description="Create a new project boundary for resources and agents.",
            input_model=ProjectCreateInput,
            output_model=ProjectResponse,
            handler=lambda session, data: ProjectService(session).create(
                ProjectCreate(**data.model_dump())
            ),
            risk="write",
            idempotent=False,
        )
    )
    registry.register(
        Capability(
            name="catalogs.create",
            module="catalogs",
            description="Create a governed data connection using a connector and Secret reference.",
            input_model=CatalogCreateInput,
            output_model=CatalogResponse,
            handler=lambda session, data: CatalogService(session).create(
                data.project_id, CatalogCreate(**_without(data, "project_id"))
            ),
            risk="write",
            idempotent=False,
        )
    )
    registry.register(
        Capability(
            name="catalogs.test_connection",
            module="catalogs",
            description="Test a Catalog without exposing its Secret.",
            input_model=CatalogIdInput,
            output_model=ConnectionTestResponse,
            handler=lambda session, data: CatalogService(session).test(data.catalog_id),
            risk="read",
        )
    )
    registry.register(
        Capability(
            name="catalogs.discover",
            module="catalogs",
            description="Discover metadata and safely mark missing resources as stale.",
            input_model=CatalogDiscoveryInput,
            output_model=DiscoveryRunResponse,
            handler=lambda session, data: CatalogService(session).discover(
                data.catalog_id, DiscoveryRequest(**_without(data, "catalog_id"))
            ),
            risk="write",
            idempotent=False,
        )
    )
    registry.register(
        Capability(
            name="knowledge_networks.create",
            module="knowledge_networks",
            description="Create a draft versioned knowledge network.",
            input_model=KnowledgeNetworkCreateInput,
            output_model=KnowledgeNetworkResponse,
            handler=lambda session, data: KnowledgeNetworkService(session).create(
                data.project_id, KnowledgeNetworkCreate(**_without(data, "project_id"))
            ),
            risk="write",
            idempotent=False,
        )
    )
    registry.register(
        Capability(
            name="knowledge_networks.create_object_type",
            module="knowledge_networks",
            description="Create a business object type with source mapping, keys and indexes.",
            input_model=ObjectTypeCreateInput,
            output_model=ObjectTypeResponse,
            handler=lambda session, data: KnowledgeNetworkService(session).create_object_type(
                data.network_id, ObjectTypeCreate(**_without(data, "network_id"))
            ),
            risk="write",
            idempotent=False,
        )
    )
    registry.register(
        Capability(
            name="knowledge_networks.create_relation_type",
            module="knowledge_networks",
            description="Create and validate a relation between two object types.",
            input_model=RelationTypeCreateInput,
            output_model=RelationTypeResponse,
            handler=lambda session, data: KnowledgeNetworkService(session).create_relation_type(
                data.network_id, RelationTypeCreate(**_without(data, "network_id"))
            ),
            risk="write",
            idempotent=False,
        )
    )
    registry.register(
        Capability(
            name="knowledge_networks.create_action_type",
            module="knowledge_networks",
            description="Create a controlled object action with impact and confirmation contracts.",
            input_model=ActionTypeCreateInput,
            output_model=ActionTypeResponse,
            handler=lambda session, data: KnowledgeNetworkService(session).create_action_type(
                data.network_id, ActionTypeCreate(**_without(data, "network_id"))
            ),
            risk="high",
            idempotent=False,
        )
    )
    registry.register(
        Capability(
            name="knowledge_networks.validate",
            module="knowledge_networks",
            description="Run whole-network validation without changing the model.",
            input_model=NetworkIdInput,
            output_model=NetworkValidationResponse,
            handler=lambda session, data: KnowledgeNetworkService(session).validate(
                data.network_id
            ),
            risk="read",
        )
    )
    registry.register(
        Capability(
            name="knowledge_networks.publish",
            module="knowledge_networks",
            description="Publish an immutable knowledge-network version after validation.",
            input_model=NetworkIdInput,
            output_model=KnowledgeNetworkResponse,
            handler=lambda session, data: KnowledgeNetworkService(session).publish(data.network_id),
            risk="high",
            idempotent=False,
        )
    )
