from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from aidp.core.schemas import APIModel, TimestampedResponse


class ConnectorTypeResponse(APIModel):
    id: str
    name: str
    mode: Literal["local", "remote"]
    categories: list[str]
    config_schema: dict[str, Any]
    capabilities: list[str]


class CatalogCreate(APIModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    connector_type: str
    secret_id: str | None = None
    config: dict[str, Any]
    scope: Literal["project", "organization", "system"] = "project"
    read_only: bool = True


class CatalogUpdate(APIModel):
    description: str | None = Field(default=None, max_length=2000)
    secret_id: str | None = None
    config: dict[str, Any] | None = None
    scope: Literal["project", "organization", "system"] | None = None
    read_only: bool | None = None


class CatalogResponse(TimestampedResponse):
    project_id: str
    name: str
    description: str
    connector_type: str
    secret_id: str | None
    config: dict[str, Any]
    scope: str
    read_only: bool
    status: str
    last_error: str | None
    last_checked_at: datetime | None


class ConnectionTestResponse(APIModel):
    ok: bool
    status: str
    latency_ms: int
    details: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class DiscoveryRequest(APIModel):
    strategy: Literal["full_sync", "create_only", "cleanup_only"] = "full_sync"
    schemas: list[str] = Field(default_factory=list)
    name_pattern: str | None = None


class DiscoveryRunResponse(TimestampedResponse):
    catalog_id: str
    strategy: str
    status: str
    scope: dict[str, Any]
    statistics: dict[str, Any]
    message: str
    started_at: datetime | None
    completed_at: datetime | None


class ResourceResponse(TimestampedResponse):
    project_id: str
    catalog_id: str
    external_id: str
    name: str
    namespace: str
    category: str
    status: str
    discovery_status: str
    resource_schema: dict[str, Any] = Field(alias="schema")
    governance: dict[str, Any]
    row_estimate: int | None


class ResourceGovernanceUpdate(APIModel):
    business_name: str | None = None
    description: str | None = None
    owner: str | None = None
    domain: str | None = None
    sensitivity: str | None = None
    tags: list[str] | None = None
