from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from aidp.core.database import get_db
from aidp.modules.catalogs.schemas import (
    CatalogCreate,
    CatalogResponse,
    CatalogUpdate,
    ConnectionTestResponse,
    ConnectorTypeResponse,
    DiscoveryRequest,
    DiscoveryRunResponse,
    ResourceGovernanceUpdate,
    ResourceResponse,
)
from aidp.modules.catalogs.service import CatalogService

router = APIRouter(tags=["data"])


@router.get("/connector-types", response_model=list[ConnectorTypeResponse])
def connector_types(session: Session = Depends(get_db)):
    return CatalogService(session).connector_types()


@router.post(
    "/projects/{project_id}/catalogs",
    response_model=CatalogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_catalog(project_id: str, payload: CatalogCreate, session: Session = Depends(get_db)):
    return CatalogService(session).create(project_id, payload)


@router.get("/projects/{project_id}/catalogs", response_model=list[CatalogResponse])
def list_catalogs(project_id: str, session: Session = Depends(get_db)):
    return CatalogService(session).list(project_id)


@router.patch("/catalogs/{catalog_id}", response_model=CatalogResponse)
def update_catalog(catalog_id: str, payload: CatalogUpdate, session: Session = Depends(get_db)):
    return CatalogService(session).update(catalog_id, payload)


@router.post("/catalogs/{catalog_id}/test", response_model=ConnectionTestResponse)
def test_catalog(catalog_id: str, session: Session = Depends(get_db)):
    return CatalogService(session).test(catalog_id)


@router.post(
    "/catalogs/{catalog_id}/discover-tasks",
    response_model=DiscoveryRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def discover_catalog(
    catalog_id: str, payload: DiscoveryRequest, session: Session = Depends(get_db)
):
    return CatalogService(session).discover(catalog_id, payload)


@router.get("/projects/{project_id}/data-resources", response_model=list[ResourceResponse])
def list_resources(project_id: str, session: Session = Depends(get_db)):
    return CatalogService(session).resources(project_id)


@router.patch("/data-resources/{resource_id}/governance", response_model=ResourceResponse)
def update_resource_governance(
    resource_id: str,
    payload: ResourceGovernanceUpdate,
    session: Session = Depends(get_db),
):
    return CatalogService(session).update_governance(resource_id, payload)
