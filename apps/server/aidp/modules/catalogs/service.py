from __future__ import annotations

from datetime import UTC, datetime

from jsonschema import Draft202012Validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aidp.core.errors import ConflictError, DomainError, NotFoundError
from aidp.modules.catalogs.connectors import CONNECTOR_DEFINITIONS, get_connector
from aidp.modules.catalogs.models import Catalog, DataResource, DiscoveryRun
from aidp.modules.catalogs.schemas import (
    CatalogCreate,
    CatalogUpdate,
    DiscoveryRequest,
    ResourceGovernanceUpdate,
)
from aidp.modules.identity.models import Secret
from aidp.modules.identity.service import IdentityService
from aidp.modules.projects.service import ProjectService


class CatalogService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def connector_types(self) -> list[dict]:
        return list(CONNECTOR_DEFINITIONS.values())

    def create(self, project_id: str, data: CatalogCreate) -> Catalog:
        ProjectService(self.session).get(project_id)
        if data.connector_type not in CONNECTOR_DEFINITIONS:
            raise DomainError("CONNECTOR_NOT_SUPPORTED", "Unsupported connector type")
        self._validate_config(data.connector_type, data.config)
        self._validate_secret(project_id, data.secret_id)
        catalog = Catalog(project_id=project_id, **data.model_dump())
        self.session.add(catalog)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("A catalog with this name already exists in the project") from exc
        self.session.refresh(catalog)
        return catalog

    def list(self, project_id: str) -> list[Catalog]:
        return list(
            self.session.scalars(
                select(Catalog).where(Catalog.project_id == project_id).order_by(Catalog.name)
            )
        )

    def get(self, catalog_id: str) -> Catalog:
        catalog = self.session.get(Catalog, catalog_id)
        if catalog is None:
            raise NotFoundError("Catalog", catalog_id)
        return catalog

    def update(self, catalog_id: str, data: CatalogUpdate) -> Catalog:
        catalog = self.get(catalog_id)
        values = data.model_dump(exclude_unset=True)
        if "config" in values and values["config"] is not None:
            self._validate_config(catalog.connector_type, values["config"])
        if "secret_id" in values:
            self._validate_secret(catalog.project_id, values["secret_id"])
        for field, value in values.items():
            setattr(catalog, field, value)
        catalog.status = "unchecked"
        self.session.commit()
        self.session.refresh(catalog)
        return catalog

    def _validate_config(self, connector_type: str, config: dict) -> None:
        schema = CONNECTOR_DEFINITIONS[connector_type]["config_schema"]
        errors = sorted(
            Draft202012Validator(schema).iter_errors(config), key=lambda item: item.path
        )
        if errors:
            message = "; ".join(error.message for error in errors[:5])
            raise DomainError("CONNECTOR_CONFIG_INVALID", message, 422)

    def _validate_secret(self, project_id: str, secret_id: str | None) -> None:
        if secret_id is None:
            return
        secret = self.session.get(Secret, secret_id)
        if secret is None or secret.project_id != project_id:
            raise DomainError(
                "INVALID_SECRET_REFERENCE", "Secret does not belong to this project", 422
            )

    def _secret(self, catalog: Catalog) -> str | None:
        if not catalog.secret_id:
            return None
        return IdentityService(self.session).reveal_secret(catalog.secret_id)

    def test(self, catalog_id: str) -> dict:
        catalog = self.get(catalog_id)
        checked_at = datetime.now(UTC)
        try:
            result = get_connector(catalog.connector_type).test(
                catalog.config, self._secret(catalog)
            )
        except Exception as exc:
            catalog.status = "unhealthy"
            catalog.last_error = str(exc)[:2000]
            catalog.last_checked_at = checked_at
            self.session.commit()
            return {
                "ok": False,
                "status": catalog.status,
                "latency_ms": 0,
                "details": {},
                "error": catalog.last_error,
            }
        catalog.status = "healthy"
        catalog.last_error = None
        catalog.last_checked_at = checked_at
        self.session.commit()
        return {
            "ok": True,
            "status": catalog.status,
            "latency_ms": result.pop("latency_ms", 0),
            "details": result,
            "error": None,
        }

    def discover(self, catalog_id: str, data: DiscoveryRequest) -> DiscoveryRun:
        catalog = self.get(catalog_id)
        run = DiscoveryRun(
            catalog_id=catalog.id,
            strategy=data.strategy,
            scope=data.model_dump(exclude={"strategy"}),
            status="running",
            started_at=datetime.now(UTC),
        )
        self.session.add(run)
        self.session.commit()
        try:
            discovered = get_connector(catalog.connector_type).discover(
                catalog.config, self._secret(catalog), run.scope
            )
            existing = {
                item.external_id: item
                for item in self.session.scalars(
                    select(DataResource).where(DataResource.catalog_id == catalog.id)
                )
            }
            seen: set[str] = set()
            counts = {"new": 0, "updated": 0, "unchanged": 0, "missing": 0}
            for item in discovered:
                seen.add(item.external_id)
                resource = existing.get(item.external_id)
                if resource is None:
                    if data.strategy == "cleanup_only":
                        continue
                    resource = DataResource(
                        project_id=catalog.project_id,
                        catalog_id=catalog.id,
                        external_id=item.external_id,
                        name=item.name,
                        namespace=item.namespace,
                        category=item.category,
                        schema=item.schema,
                        row_estimate=item.row_estimate,
                        last_seen_run_id=run.id,
                        discovery_status="new",
                    )
                    self.session.add(resource)
                    counts["new"] += 1
                else:
                    changed = resource.schema != item.schema or resource.status == "stale"
                    resource.name = item.name
                    resource.namespace = item.namespace
                    resource.category = item.category
                    resource.schema = item.schema
                    resource.row_estimate = item.row_estimate
                    resource.status = "active"
                    resource.last_seen_run_id = run.id
                    resource.discovery_status = "updated" if changed else "unchanged"
                    counts[resource.discovery_status] += 1
            if data.strategy in {"full_sync", "cleanup_only"}:
                for external_id, resource in existing.items():
                    if external_id not in seen:
                        resource.status = "stale"
                        resource.discovery_status = "missing"
                        counts["missing"] += 1
            run.status = "completed"
            run.statistics = counts
            run.message = f"Discovered {len(discovered)} resources"
            run.completed_at = datetime.now(UTC)
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            run = self.session.get(DiscoveryRun, run.id)
            if run is None:
                raise
            run.status = "failed"
            run.message = str(exc)[:2000]
            run.completed_at = datetime.now(UTC)
            self.session.commit()
        self.session.refresh(run)
        return run

    def resources(self, project_id: str) -> list[DataResource]:
        return list(
            self.session.scalars(
                select(DataResource)
                .where(DataResource.project_id == project_id)
                .order_by(DataResource.namespace, DataResource.name)
            )
        )

    def update_governance(self, resource_id: str, data: ResourceGovernanceUpdate) -> DataResource:
        resource = self.session.get(DataResource, resource_id)
        if resource is None:
            raise NotFoundError("DataResource", resource_id)
        resource.governance = {
            **resource.governance,
            **data.model_dump(exclude_none=True),
        }
        self.session.commit()
        self.session.refresh(resource)
        return resource
