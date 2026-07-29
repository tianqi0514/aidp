"""Import all SQLAlchemy models so Alembic can discover them."""

from aidp.modules.capabilities.models import CapabilityInvocation
from aidp.modules.catalogs.models import Catalog, DataResource, DiscoveryRun
from aidp.modules.identity.models import ProjectMember, Secret, User
from aidp.modules.knowledge_networks.models import (
    ActionType,
    KnowledgeNetwork,
    ObjectType,
    RelationType,
)
from aidp.modules.projects.models import Project

__all__ = [
    "ActionType",
    "CapabilityInvocation",
    "Catalog",
    "DataResource",
    "DiscoveryRun",
    "KnowledgeNetwork",
    "ObjectType",
    "Project",
    "ProjectMember",
    "RelationType",
    "Secret",
    "User",
]
