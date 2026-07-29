from typing import Any, Literal

from pydantic import Field, model_validator

from aidp.core.schemas import APIModel, TimestampedResponse


class KnowledgeNetworkCreate(APIModel):
    key: str = Field(pattern="^[a-z][a-z0-9_]{1,98}[a-z0-9]$")
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)
    branch: str = Field(default="main", max_length=100)
    concept_groups: list[dict[str, Any]] = Field(default_factory=list)


class KnowledgeNetworkResponse(TimestampedResponse):
    project_id: str
    key: str
    name: str
    description: str
    version: int
    branch: str
    status: str
    concept_groups: list[dict[str, Any]]


class ObjectProperty(APIModel):
    key: str = Field(pattern="^[a-z][a-z0-9_]{0,99}$")
    name: str = Field(min_length=1, max_length=160)
    data_type: Literal[
        "integer",
        "unsigned_integer",
        "float",
        "decimal",
        "string",
        "text",
        "date",
        "timestamp",
        "time",
        "datetime",
        "boolean",
        "binary",
        "json",
        "vector",
        "point",
        "shape",
        "ip",
    ]
    nullable: bool = True
    source_field: str | None = None
    default: Any | None = None
    enum: list[Any] | None = None
    sensitivity: str = "internal"
    description: str = ""
    logical_expression: dict[str, Any] | None = None


class ObjectTypeCreate(APIModel):
    key: str = Field(pattern="^[a-z][a-z0-9_]{1,98}[a-z0-9]$")
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)
    concept_group: str | None = None
    source_resource_id: str | None = None
    properties: list[ObjectProperty] = Field(min_length=1)
    primary_keys: list[str] = Field(min_length=1)
    display_key: str | None = None
    incremental_key: str | None = None
    indexes: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_keys(self):
        keys = {prop.key for prop in self.properties}
        referenced = set(self.primary_keys)
        referenced.update(key for key in [self.display_key, self.incremental_key] if key)
        missing = referenced - keys
        if missing:
            raise ValueError(f"Keys reference missing properties: {sorted(missing)}")
        if len(keys) != len(self.properties):
            raise ValueError("Property keys must be unique")
        return self


class ObjectTypeResponse(TimestampedResponse):
    network_id: str
    key: str
    name: str
    description: str
    concept_group: str | None
    source_resource_id: str | None
    properties: list[dict[str, Any]]
    primary_keys: list[str]
    display_key: str | None
    incremental_key: str | None
    indexes: list[dict[str, Any]]
    status: str


class RelationTypeCreate(APIModel):
    key: str = Field(pattern="^[a-z][a-z0-9_]{1,98}[a-z0-9]$")
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)
    source_object_type_id: str
    target_object_type_id: str
    cardinality: Literal["one_to_one", "one_to_many", "many_to_many"]
    mapping_type: Literal["direct", "data_view", "filtered_cross_join"]
    mapping: dict[str, Any]
    properties: list[ObjectProperty] = Field(default_factory=list)


class RelationTypeResponse(TimestampedResponse):
    network_id: str
    key: str
    name: str
    description: str
    source_object_type_id: str
    target_object_type_id: str
    cardinality: str
    mapping_type: str
    mapping: dict[str, Any]
    properties: list[dict[str, Any]]


class ActionTypeCreate(APIModel):
    key: str = Field(pattern="^[a-z][a-z0-9_]{1,98}[a-z0-9]$")
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)
    operation: Literal["add", "modify", "delete"]
    object_type_id: str
    condition: dict[str, Any] = Field(default_factory=dict)
    impact_contract: dict[str, Any]
    parameters_schema: dict[str, Any]
    executor: dict[str, Any]
    permission: Literal["allow", "ask", "deny"] = "ask"
    retry_policy: dict[str, Any] = Field(default_factory=dict)
    compensation: dict[str, Any] = Field(default_factory=dict)


class ActionTypeResponse(TimestampedResponse):
    network_id: str
    key: str
    name: str
    description: str
    operation: str
    object_type_id: str
    condition: dict[str, Any]
    impact_contract: dict[str, Any]
    parameters_schema: dict[str, Any]
    executor: dict[str, Any]
    permission: str
    retry_policy: dict[str, Any]
    compensation: dict[str, Any]


class ValidationIssue(APIModel):
    level: Literal["error", "warning"]
    code: str
    message: str
    resource_type: str
    resource_id: str | None = None


class NetworkValidationResponse(APIModel):
    valid: bool
    issues: list[ValidationIssue]
    summary: dict[str, int]
