from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from aidp.core.database import get_db
from aidp.modules.identity.schemas import (
    MemberCreate,
    MemberResponse,
    SecretCreate,
    SecretResponse,
    UserCreate,
    UserResponse,
)
from aidp.modules.identity.service import IdentityService

router = APIRouter(tags=["identity"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, session: Session = Depends(get_db)):
    return IdentityService(session).create_user(payload)


@router.get("/users", response_model=list[UserResponse])
def list_users(session: Session = Depends(get_db)):
    return IdentityService(session).list_users()


@router.post(
    "/projects/{project_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(project_id: str, payload: MemberCreate, session: Session = Depends(get_db)):
    return IdentityService(session).add_member(project_id, payload)


@router.post(
    "/projects/{project_id}/secrets",
    response_model=SecretResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_secret(project_id: str, payload: SecretCreate, session: Session = Depends(get_db)):
    return IdentityService(session).create_secret(project_id, payload)


@router.get("/projects/{project_id}/secrets", response_model=list[SecretResponse])
def list_secrets(project_id: str, session: Session = Depends(get_db)):
    return IdentityService(session).list_secrets(project_id)
