from datetime import datetime

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class TimestampedResponse(APIModel):
    id: str
    created_at: datetime
    updated_at: datetime


class HealthResponse(APIModel):
    status: str
    service: str
    version: str


class ErrorResponse(APIModel):
    code: str
    message: str
    request_id: str
