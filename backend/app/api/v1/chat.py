"""Chat session and message REST API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select

from app.core.deps import CurrentUserID, DBSession
from app.models.claw import Claw
from app.models.permission import ClawPermission, PermissionRole
from app.models.session import ChatMessage, ChatSession

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class SessionResponse(BaseModel):
    id: UUID
    claw_id: UUID
    user_id: UUID
    title: str
    is_active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class CreateSessionRequest(BaseModel):
    title: str = "New Session"


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    tool_calls: list | None
    tool_call_id: str | None
    tool_name: str | None
    input_tokens: int | None
    output_tokens: int | None
    created_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _check_access(
    db: DBSession,
    claw_id: UUID,
    user_id: UUID,
    *required_roles: PermissionRole,
) -> Claw:
    result = await db.execute(select(Claw).where(Claw.id == claw_id))
    claw = result.scalar_one_or_none()
    if not claw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claw not found")

    if claw.owner_id == user_id:
        return claw

    result2 = await db.execute(
        select(ClawPermission).where(
            ClawPermission.claw_id == claw_id,
            ClawPermission.user_id == user_id,
        )
    )
    perm = result2.scalar_one_or_none()
    if not perm or (required_roles and perm.role not in required_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return claw


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------


@router.get("/{claw_id}/sessions", response_model=list[SessionResponse])
async def list_sessions(
    claw_id: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> list[ChatSession]:
    await _check_access(
        db, claw_id, current_user_id,
        PermissionRole.OWNER, PermissionRole.COLLABORATOR,
    )

    result = await db.execute(
        select(ChatSession)
        .where(
            ChatSession.claw_id == claw_id,
            ChatSession.user_id == current_user_id,
            ChatSession.is_active.is_(True),
        )
        .order_by(ChatSession.updated_at.desc())
    )
    return list(result.scalars().all())


@router.post(
    "/{claw_id}/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    claw_id: UUID,
    body: CreateSessionRequest,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> ChatSession:
    await _check_access(
        db, claw_id, current_user_id,
        PermissionRole.OWNER, PermissionRole.COLLABORATOR,
    )

    session = ChatSession(
        claw_id=claw_id,
        user_id=current_user_id,
        title=body.title,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


@router.get("/{claw_id}/sessions/{sid}/messages", response_model=list[MessageResponse])
async def get_messages(
    claw_id: UUID,
    sid: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
    limit: int = Query(100, ge=1, le=500),
    before: UUID | None = None,
) -> list[ChatMessage]:
    await _check_access(
        db, claw_id, current_user_id,
        PermissionRole.OWNER, PermissionRole.COLLABORATOR, PermissionRole.VIEWER,
    )

    result = await db.execute(select(ChatSession).where(ChatSession.id == sid))
    session = result.scalar_one_or_none()
    if not session or session.claw_id != claw_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    query = (
        select(ChatMessage)
        .where(ChatMessage.session_id == sid)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    if before:
        # Cursor-based pagination
        ref_result = await db.execute(
            select(ChatMessage.created_at).where(ChatMessage.id == before)
        )
        ref_ts = ref_result.scalar_one_or_none()
        if ref_ts:
            query = query.where(ChatMessage.created_at < ref_ts)

    result2 = await db.execute(query)
    messages = list(result2.scalars().all())
    messages.reverse()  # Return in chronological order
    return messages


@router.delete("/{claw_id}/sessions/{sid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    claw_id: UUID,
    sid: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> None:
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == sid,
            ChatSession.claw_id == claw_id,
            ChatSession.user_id == current_user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    await db.delete(session)