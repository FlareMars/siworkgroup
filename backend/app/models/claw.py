"""Claw (OpenClaw agent instance) model."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ClawStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    DESTROYED = "destroyed"


class Claw(Base):
    __tablename__ = "claws"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    status: Mapped[ClawStatus] = mapped_column(
        String(20),
        default=ClawStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Owner
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Container info
    container_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    container_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Model configuration
    model: Mapped[str] = mapped_column(String(100), default="gpt-4o", nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Sandbox configuration (JSON)
    sandbox_config: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # Enabled tools (JSON array of tool names)
    enabled_tools: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    # Working directory inside container
    work_dir: Mapped[str] = mapped_column(
        String(512), default="/workspace", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    owner: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="owned_claws",
        foreign_keys=[owner_id],
    )
    permissions: Mapped[list["ClawPermission"]] = relationship(  # noqa: F821
        "ClawPermission",
        back_populates="claw",
        cascade="all, delete-orphan",
    )
    policy: Mapped["ClawPolicy | None"] = relationship(  # noqa: F821
        "ClawPolicy",
        back_populates="claw",
        uselist=False,
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["ChatSession"]] = relationship(  # noqa: F821
        "ChatSession",
        back_populates="claw",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # noqa: F821
        "AuditLog",
        back_populates="claw",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Claw id={self.id} name={self.name!r} status={self.status}>"