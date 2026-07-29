from pydantic import Field

from aidp.core.schemas import APIModel, TimestampedResponse


class ProjectCreate(APIModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(pattern="^[a-z0-9][a-z0-9-]{1,78}[a-z0-9]$")
    description: str = Field(default="", max_length=2000)
    timezone: str = Field(default="Asia/Shanghai", max_length=64)


class ProjectUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(default=None, pattern="^(active|archived)$")
    timezone: str | None = Field(default=None, max_length=64)


class ProjectResponse(TimestampedResponse):
    name: str
    slug: str
    description: str
    status: str
    timezone: str
