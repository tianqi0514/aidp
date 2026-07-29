from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from aidp.core.database import Base
from aidp.core.models import TimestampMixin, UUIDPrimaryKeyMixin


class Catalog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "catalogs"
    __table_args__ = (UniqueConstraint("project_id", "name"),)

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    connector_type: Mapped[str] = mapped_column(String(64), index=True)
    secret_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("secrets.id", ondelete="RESTRICT"), nullable=True
    )
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    scope: Mapped[str] = mapped_column(String(24), default="project")
    read_only: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(24), default="unchecked", index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DiscoveryRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "discovery_runs"

    catalog_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("catalogs.id", ondelete="CASCADE"), index=True
    )
    strategy: Mapped[str] = mapped_column(String(32), default="full_sync")
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    scope: Mapped[dict] = mapped_column(JSON, default=dict)
    statistics: Mapped[dict] = mapped_column(JSON, default=dict)
    message: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DataResource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "data_resources"
    __table_args__ = (UniqueConstraint("catalog_id", "external_id"),)

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    catalog_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("catalogs.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(500))
    name: Mapped[str] = mapped_column(String(255), index=True)
    namespace: Mapped[str] = mapped_column(String(500), default="")
    category: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(24), default="active", index=True)
    discovery_status: Mapped[str] = mapped_column(String(24), default="new")
    schema: Mapped[dict] = mapped_column(JSON, default=dict)
    governance: Mapped[dict] = mapped_column(JSON, default=dict)
    row_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_seen_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
