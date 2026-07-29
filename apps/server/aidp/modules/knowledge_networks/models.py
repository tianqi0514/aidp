from sqlalchemy import JSON, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from aidp.core.database import Base
from aidp.core.models import TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeNetwork(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_networks"
    __table_args__ = (UniqueConstraint("project_id", "key", "version"),)

    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    branch: Mapped[str] = mapped_column(String(100), default="main")
    status: Mapped[str] = mapped_column(String(24), default="draft", index=True)
    concept_groups: Mapped[list] = mapped_column(JSON, default=list)


class ObjectType(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "object_types"
    __table_args__ = (UniqueConstraint("network_id", "key"),)

    network_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_networks.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    concept_group: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_resource_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("data_resources.id", ondelete="RESTRICT"), nullable=True
    )
    properties: Mapped[list] = mapped_column(JSON, default=list)
    primary_keys: Mapped[list] = mapped_column(JSON, default=list)
    display_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    incremental_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    indexes: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(24), default="active")


class RelationType(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "relation_types"
    __table_args__ = (UniqueConstraint("network_id", "key"),)

    network_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_networks.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    source_object_type_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("object_types.id", ondelete="CASCADE")
    )
    target_object_type_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("object_types.id", ondelete="CASCADE")
    )
    cardinality: Mapped[str] = mapped_column(String(32), default="many_to_many")
    mapping_type: Mapped[str] = mapped_column(String(40), default="direct")
    mapping: Mapped[dict] = mapped_column(JSON, default=dict)
    properties: Mapped[list] = mapped_column(JSON, default=list)


class ActionType(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "action_types"
    __table_args__ = (UniqueConstraint("network_id", "key"),)

    network_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_networks.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    operation: Mapped[str] = mapped_column(String(24))
    object_type_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("object_types.id", ondelete="CASCADE")
    )
    condition: Mapped[dict] = mapped_column(JSON, default=dict)
    impact_contract: Mapped[dict] = mapped_column(JSON, default=dict)
    parameters_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    executor: Mapped[dict] = mapped_column(JSON, default=dict)
    permission: Mapped[str] = mapped_column(String(24), default="ask")
    retry_policy: Mapped[dict] = mapped_column(JSON, default=dict)
    compensation: Mapped[dict] = mapped_column(JSON, default=dict)
