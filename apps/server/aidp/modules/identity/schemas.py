from datetime import datetime

from pydantic import EmailStr, Field

from aidp.core.schemas import APIModel, TimestampedResponse


class UserCreate(APIModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=120)


class UserResponse(TimestampedResponse):
    email: str
    display_name: str
    is_active: bool


class MemberCreate(APIModel):
    user_id: str
    role: str = Field(pattern="^(admin|editor|viewer)$")


class MemberResponse(TimestampedResponse):
    project_id: str
    user_id: str
    role: str


class SecretCreate(APIModel):
    name: str = Field(min_length=1, max_length=120)
    kind: str = Field(default="credentials", max_length=40)
    value: str = Field(min_length=1)


class SecretResponse(APIModel):
    id: str
    project_id: str
    name: str
    kind: str
    created_at: datetime
    updated_at: datetime
