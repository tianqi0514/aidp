from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from aidp.core.database import get_db
from aidp.modules.projects.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from aidp.modules.projects.service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, session: Session = Depends(get_db)):
    return ProjectService(session).create(payload)


@router.get("", response_model=list[ProjectResponse])
def list_projects(session: Session = Depends(get_db)):
    return ProjectService(session).list()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, session: Session = Depends(get_db)):
    return ProjectService(session).get(project_id)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, payload: ProjectUpdate, session: Session = Depends(get_db)):
    return ProjectService(session).update(project_id, payload)
