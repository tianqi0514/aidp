import base64
import hashlib

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.orm import Session

from aidp.core.config import get_settings
from aidp.core.errors import ConflictError, NotFoundError
from aidp.modules.identity.models import ProjectMember, Secret, User
from aidp.modules.identity.schemas import MemberCreate, SecretCreate, UserCreate


def _fernet() -> Fernet:
    digest = hashlib.sha256(get_settings().secret_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


class IdentityService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_user(self, data: UserCreate) -> User:
        if self.session.scalar(select(User).where(User.email == data.email)):
            raise ConflictError("A user with this email already exists")
        user = User(**data.model_dump())
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def list_users(self) -> list[User]:
        return list(self.session.scalars(select(User).order_by(User.created_at)))

    def add_member(self, project_id: str, data: MemberCreate) -> ProjectMember:
        if self.session.get(User, data.user_id) is None:
            raise NotFoundError("User", data.user_id)
        existing = self.session.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id, ProjectMember.user_id == data.user_id
            )
        )
        if existing:
            raise ConflictError("The user is already a member of this project")
        member = ProjectMember(project_id=project_id, **data.model_dump())
        self.session.add(member)
        self.session.commit()
        self.session.refresh(member)
        return member

    def create_secret(self, project_id: str, data: SecretCreate) -> Secret:
        if self.session.scalar(
            select(Secret).where(Secret.project_id == project_id, Secret.name == data.name)
        ):
            raise ConflictError("A secret with this name already exists in the project")
        secret = Secret(
            project_id=project_id,
            name=data.name,
            kind=data.kind,
            encrypted_value=_fernet().encrypt(data.value.encode()).decode(),
        )
        self.session.add(secret)
        self.session.commit()
        self.session.refresh(secret)
        return secret

    def reveal_secret(self, secret_id: str) -> str:
        secret = self.session.get(Secret, secret_id)
        if secret is None:
            raise NotFoundError("Secret", secret_id)
        return _fernet().decrypt(secret.encrypted_value.encode()).decode()

    def list_secrets(self, project_id: str) -> list[Secret]:
        return list(
            self.session.scalars(
                select(Secret).where(Secret.project_id == project_id).order_by(Secret.name)
            )
        )
