"""Permission and policy models."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PermissionRole(str, Enum):
    OWNER = "owner"
    COLLABORATOR = "collaborator"
    VIEWER = "viewer"


class ClawPermission(Base):
    """Maps a user to a Claw with a specific role."""

    __tablename__ = "claw_permissions"
    __table_args__ = (
        UniqueConstraint("claw_id", "user_id", name="uq_claw_user_permission"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    claw_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claws.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[PermissionRole] = mapped_column(
        String(20), default=PermissionRole.VIEWER, nullable=False
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
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

    # Relationships
    claw: Mapped["Claw"] = relationship("Claw", back_populates="permissions")  # noqa: F821
    user: Mapped["User"] = relationship("User", back_populates="permissions")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<ClawPermission claw={self.claw_id} user={self.user_id} role={self.role}>"
        )


class ClawPolicy(Base):
    """Resource access policy for a Claw."""

    __tablename__ = "claw_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    claw_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claws.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Network policy: {"egress_whitelist": [...], "allow_localhost": true}
    network_policy: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Filesystem policy: {"writable_paths": [...], "readonly_paths": [...], "blocked_paths": [...]}
    fs_policy: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Command blacklist: list of regex patterns
    command_blacklist: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # API key policies: {"keys": [{"id": ..., "scopes": [...], "expires_at": ...}]}
    api_keys: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

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

    # Relationships
    claw: Mapped["Claw"] = relationship("Claw", back_populates="policy")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ClawPolicy claw={self.claw_id}>"