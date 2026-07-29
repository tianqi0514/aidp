from fastapi import APIRouter, Depends
from pydantic import ValidationError
from sqlalchemy.orm import Session

from aidp.core.database import get_db
from aidp.modules.capabilities.registry import registry
from aidp.modules.capabilities.schemas import (
    CapabilityInvokeRequest,
    CapabilityInvokeResponse,
    CapabilityPlanRequest,
    CapabilityPlanResponse,
    CapabilityResponse,
)

router = APIRouter(prefix="/agent/capabilities", tags=["agent-capabilities"])


@router.get("", response_model=list[CapabilityResponse])
def list_capabilities():
    return [item.descriptor() for item in registry.list()]


@router.post("/validate-plan", response_model=CapabilityPlanResponse)
def validate_plan(payload: CapabilityPlanRequest):
    results = []
    for step in payload.steps:
        errors: list[str] = []
        risk = None
        confirmation = False
        try:
            capability = registry.get(step.capability)
            risk = capability.risk
            confirmation = risk in {"write", "high"}
            capability.input_model.model_validate(step.input)
            if confirmation and not step.confirmed:
                errors.append("Execution requires explicit confirmation")
        except (ValidationError, Exception) as exc:
            if not errors or not isinstance(exc, ValidationError):
                errors.append(str(exc))
        results.append(
            {
                "id": step.id,
                "valid": not errors,
                "capability": step.capability,
                "risk": risk,
                "requires_confirmation": confirmation,
                "errors": errors,
            }
        )
    return {"valid": all(item["valid"] for item in results), "steps": results}


@router.post("/{capability_name}:invoke", response_model=CapabilityInvokeResponse)
def invoke_capability(
    capability_name: str,
    payload: CapabilityInvokeRequest,
    session: Session = Depends(get_db),
):
    return registry.invoke(
        session,
        capability_name,
        payload.input,
        mode=payload.mode,
        confirmed=payload.confirmed,
        actor_id=payload.actor_id,
    )
