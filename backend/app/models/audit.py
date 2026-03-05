"""Audit log model - append-only, immutable records."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditLog(Base):
    """Immutable audit log entry.
    
    Records all significant actions: permission changes, Claw lifecycle events,
    chat sessions, policy updates, etc. Once written, rows are never modified.
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    claw_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("claws.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Action category: claw.start, claw.stop, permission.grant, etc.
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Human-readable description
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Arbitrary structured context (before/after state, parameters, etc.)
    context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # IP address of the request originator (if applicable)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Immutable timestamp - never use onupdate here
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    claw: Mapped["Claw | None"] = relationship("Claw", back_populates="audit_logs")  # noqa: F821

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action!r} claw={self.claw_id}>"