from typing import Any, Literal

from pydantic import Field

from aidp.core.schemas import APIModel


class CapabilityResponse(APIModel):
    name: str
    module: str
    description: str
    risk: Literal["read", "write", "high"]
    idempotent: bool
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]


class CapabilityInvokeRequest(APIModel):
    input: dict[str, Any]
    mode: Literal["preview", "execute"] = "preview"
    confirmed: bool = False
    actor_id: str | None = None


class CapabilityInvokeResponse(APIModel):
    invocation_id: str | None = None
    capability: str
    mode: str
    status: str
    requires_confirmation: bool
    output: dict[str, Any] = Field(default_factory=dict)


class PlanStep(APIModel):
    id: str
    capability: str
    input: dict[str, Any]
    confirmed: bool = False


class CapabilityPlanRequest(APIModel):
    steps: list[PlanStep] = Field(min_length=1, max_length=50)


class PlanStepValidation(APIModel):
    id: str
    valid: bool
    capability: str
    risk: str | None = None
    requires_confirmation: bool = False
    errors: list[str] = Field(default_factory=list)


class CapabilityPlanResponse(APIModel):
    valid: bool
    steps: list[PlanStepValidation]
