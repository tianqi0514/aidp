from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from aidp.core.database import get_db
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

router = APIRouter(tags=["knowledge-networks"])


@router.post(
    "/projects/{project_id}/knowledge-networks",
    response_model=KnowledgeNetworkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_network(
    project_id: str,
    payload: KnowledgeNetworkCreate,
    session: Session = Depends(get_db),
):
    return KnowledgeNetworkService(session).create(project_id, payload)


@router.get(
    "/projects/{project_id}/knowledge-networks",
    response_model=list[KnowledgeNetworkResponse],
)
def list_networks(project_id: str, session: Session = Depends(get_db)):
    return KnowledgeNetworkService(session).list(project_id)


@router.post(
    "/knowledge-networks/{network_id}/object-types",
    response_model=ObjectTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_object_type(
    network_id: str, payload: ObjectTypeCreate, session: Session = Depends(get_db)
):
    return KnowledgeNetworkService(session).create_object_type(network_id, payload)


@router.get(
    "/knowledge-networks/{network_id}/object-types",
    response_model=list[ObjectTypeResponse],
)
def list_object_types(network_id: str, session: Session = Depends(get_db)):
    return KnowledgeNetworkService(session).list_object_types(network_id)


@router.post(
    "/knowledge-networks/{network_id}/relation-types",
    response_model=RelationTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_relation_type(
    network_id: str, payload: RelationTypeCreate, session: Session = Depends(get_db)
):
    return KnowledgeNetworkService(session).create_relation_type(network_id, payload)


@router.get(
    "/knowledge-networks/{network_id}/relation-types",
    response_model=list[RelationTypeResponse],
)
def list_relation_types(network_id: str, session: Session = Depends(get_db)):
    return KnowledgeNetworkService(session).list_relation_types(network_id)


@router.post(
    "/knowledge-networks/{network_id}/action-types",
    response_model=ActionTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_action_type(
    network_id: str, payload: ActionTypeCreate, session: Session = Depends(get_db)
):
    return KnowledgeNetworkService(session).create_action_type(network_id, payload)


@router.get(
    "/knowledge-networks/{network_id}/action-types",
    response_model=list[ActionTypeResponse],
)
def list_action_types(network_id: str, session: Session = Depends(get_db)):
    return KnowledgeNetworkService(session).list_action_types(network_id)


@router.post("/knowledge-networks/{network_id}/validate", response_model=NetworkValidationResponse)
def validate_network(network_id: str, session: Session = Depends(get_db)):
    return KnowledgeNetworkService(session).validate(network_id)


@router.post("/knowledge-networks/{network_id}/publish", response_model=KnowledgeNetworkResponse)
def publish_network(network_id: str, session: Session = Depends(get_db)):
    return KnowledgeNetworkService(session).publish(network_id)
