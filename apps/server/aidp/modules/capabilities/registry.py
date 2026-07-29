from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from aidp.core.errors import DomainError
from aidp.modules.capabilities.models import CapabilityInvocation

CapabilityRisk = Literal["read", "write", "high"]
CapabilityHandler = Callable[[Session, BaseModel], Any]


@dataclass(frozen=True)
class Capability:
    name: str
    module: str
    description: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    handler: CapabilityHandler
    risk: CapabilityRisk = "read"
    idempotent: bool = True

    def descriptor(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "module": self.module,
            "description": self.description,
            "risk": self.risk,
            "idempotent": self.idempotent,
            "input_schema": self.input_model.model_json_schema(),
            "output_schema": self.output_model.model_json_schema(),
        }


class CapabilityRegistry:
    def __init__(self) -> None:
        self._items: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        if capability.name in self._items:
            raise RuntimeError(f"Capability already registered: {capability.name}")
        self._items[capability.name] = capability

    def get(self, name: str) -> Capability:
        try:
            return self._items[name]
        except KeyError as exc:
            raise DomainError("CAPABILITY_NOT_FOUND", f"Unknown capability: {name}", 404) from exc

    def list(self) -> list[Capability]:
        return sorted(self._items.values(), key=lambda item: (item.module, item.name))

    def clear(self) -> None:
        self._items.clear()

    def validate_input(self, name: str, payload: dict[str, Any]) -> BaseModel:
        capability = self.get(name)
        try:
            return capability.input_model.model_validate(payload)
        except ValidationError as exc:
            raise DomainError("CAPABILITY_INPUT_INVALID", str(exc), 422) from exc

    def invoke(
        self,
        session: Session,
        name: str,
        payload: dict[str, Any],
        *,
        mode: str,
        confirmed: bool,
        actor_id: str | None,
    ) -> dict[str, Any]:
        capability = self.get(name)
        parsed = self.validate_input(name, payload)
        requires_confirmation = capability.risk in {"write", "high"}
        if mode == "preview":
            return {
                "invocation_id": None,
                "capability": name,
                "mode": mode,
                "status": "validated",
                "requires_confirmation": requires_confirmation,
                "output": {
                    "validated_input": parsed.model_dump(mode="json"),
                    "description": capability.description,
                },
            }
        if requires_confirmation and not confirmed:
            raise DomainError(
                "CAPABILITY_CONFIRMATION_REQUIRED",
                f"Capability '{name}' requires explicit confirmation",
                409,
            )
        invocation = CapabilityInvocation(
            capability_name=name,
            actor_id=actor_id,
            mode=mode,
            status="running",
            input_data=parsed.model_dump(mode="json"),
        )
        session.add(invocation)
        session.commit()
        try:
            raw_output = capability.handler(session, parsed)
            output = capability.output_model.model_validate(raw_output).model_dump(mode="json")
            invocation.status = "completed"
            invocation.output_data = output
            session.commit()
            return {
                "invocation_id": invocation.id,
                "capability": name,
                "mode": mode,
                "status": "completed",
                "requires_confirmation": requires_confirmation,
                "output": output,
            }
        except Exception as exc:
            session.rollback()
            invocation = session.get(CapabilityInvocation, invocation.id)
            if invocation is not None:
                invocation.status = "failed"
                invocation.error = str(exc)[:4000]
                session.commit()
            raise


registry = CapabilityRegistry()
