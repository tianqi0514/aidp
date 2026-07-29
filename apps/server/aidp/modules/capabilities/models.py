from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from aidp.core.database import Base
from aidp.core.models import TimestampMixin, UUIDPrimaryKeyMixin


class CapabilityInvocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "capability_invocations"

    capability_name: Mapped[str] = mapped_column(String(180), index=True)
    actor_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    mode: Mapped[str] = mapped_column(String(24), default="execute")
    status: Mapped[str] = mapped_column(String(24), index=True)
    input_data: Mapped[dict] = mapped_column(JSON, default=dict)
    output_data: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
