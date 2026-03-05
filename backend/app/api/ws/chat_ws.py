"""WebSocket endpoint for real-time chat with a Claw."""

import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import decode_token
from app.models.claw import Claw, ClawStatus
from app.models.permission import ClawPermission, PermissionRole
from app.models.session import ChatMessage, ChatSession, MessageRole

router = APIRouter()


async def _authenticate_ws(websocket: WebSocket) -> UUID | None:
    """Extract user ID from WebSocket query token or Authorization header."""
    # Try query parameter first (common for WS clients)
    token = websocket.query_params.get("token")
    if not token:
        # Try Authorization header
        auth = websocket.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]

    if not token:
        return None

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        return UUID(payload["sub"])
    except (JWTError, ValueError, KeyError):
        return None


@router.websocket("/ws/claws/{claw_id}/sessions/{session_id}/chat")
async def chat_websocket(
    websocket: WebSocket,
    claw_id: UUID,
    session_id: UUID,
) -> None:
    """
    WebSocket endpoint for real-time streaming chat with a Claw.

    Protocol:
    - Client sends: {"type": "message", "content": "user text"}
    - Server sends: {"type": "chunk", "content": "...", "done": false}
    - Server sends: {"type": "chunk", "content": "...", "done": true}
    - Server sends: {"type": "error", "detail": "..."}
    - Server sends: {"type": "ping"}
    """
    await websocket.accept()

    # Authenticate
    user_id = await _authenticate_ws(websocket)
    if not user_id:
        await websocket.send_json({"type": "error", "detail": "Unauthorized"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    async with AsyncSessionLocal() as db:
        # Validate claw and session
        result = await db.execute(select(Claw).where(Claw.id == claw_id))
        claw = result.scalar_one_or_none()
        if not claw:
            await websocket.send_json({"type": "error", "detail": "Claw not found"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Check permission
        has_access = claw.owner_id == user_id
        if not has_access:
            perm_result = await db.execute(
                select(ClawPermission).where(
                    ClawPermission.claw_id == claw_id,
                    ClawPermission.user_id == user_id,
                    ClawPermission.role.in_(
                        [PermissionRole.OWNER, PermissionRole.COLLABORATOR]
                    ),
                )
            )
            has_access = perm_result.scalar_one_or_none() is not None

        if not has_access:
            await websocket.send_json({"type": "error", "detail": "Forbidden"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Validate session
        sess_result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.claw_id == claw_id,
            )
        )
        chat_session = sess_result.scalar_one_or_none()
        if not chat_session:
            await websocket.send_json({"type": "error", "detail": "Session not found"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if claw.status != ClawStatus.RUNNING:
            await websocket.send_json(
                {"type": "error", "detail": "Claw is not running"}
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    # Main message loop
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "detail": "Invalid JSON"})
                continue

            msg_type = msg.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type != "message":
                await websocket.send_json(
                    {"type": "error", "detail": f"Unknown message type: {msg_type!r}"}
                )
                continue

            content = msg.get("content", "").strip()
            if not content:
                await websocket.send_json({"type": "error", "detail": "Empty message"})
                continue

            # Persist user message
            async with AsyncSessionLocal() as db:
                user_msg = ChatMessage(
                    session_id=session_id,
                    role=MessageRole.USER,
                    content=content,
                )
                db.add(user_msg)
                await db.commit()

            # TODO: Forward to Claw via chat_service and stream the response
            # For now, echo the message back as a placeholder
            await websocket.send_json(
                {"type": "chunk", "content": f"[Echo] {content}", "done": False}
            )
            await websocket.send_json(
                {"type": "chunk", "content": "", "done": True}
            )

    except WebSocketDisconnect:
        pass