from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aidp.core.errors import ConflictError, NotFoundError
from aidp.modules.projects.models import Project
from aidp.modules.projects.schemas import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: ProjectCreate) -> Project:
        project = Project(**data.model_dump())
        self.session.add(project)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("A project with this slug already exists") from exc
        self.session.refresh(project)
        return project

    def list(self) -> list[Project]:
        return list(self.session.scalars(select(Project).order_by(Project.created_at.desc())))

    def get(self, project_id: str) -> Project:
        project = self.session.get(Project, project_id)
        if project is None:
            raise NotFoundError("Project", project_id)
        return project

    def update(self, project_id: str, data: ProjectUpdate) -> Project:
        project = self.get(project_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        self.session.commit()
        self.session.refresh(project)
        return project
