"""Permission management API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.core.deps import CurrentUserID, DBSession
from app.models.audit import AuditLog
from app.models.claw import Claw
from app.models.permission import ClawPermission, ClawPolicy, PermissionRole
from app.models.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class PermissionResponse(BaseModel):
    id: UUID
    claw_id: UUID
    user_id: UUID
    role: PermissionRole
    granted_by: UUID | None
    created_at: str

    model_config = {"from_attributes": True}


class AddPermissionRequest(BaseModel):
    user_id: UUID
    role: PermissionRole


class UpdatePermissionRequest(BaseModel):
    role: PermissionRole


class PolicyResponse(BaseModel):
    id: UUID
    claw_id: UUID
    network_policy: dict
    fs_policy: dict
    command_blacklist: list
    api_keys: list
    updated_at: str

    model_config = {"from_attributes": True}


class UpdatePolicyRequest(BaseModel):
    network_policy: dict | None = None
    fs_policy: dict | None = None
    command_blacklist: list | None = None


class AuditLogResponse(BaseModel):
    id: UUID
    claw_id: UUID | None
    actor_id: UUID | None
    action: str
    description: str
    context: dict
    ip_address: str | None
    created_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _require_owner(db: DBSession, claw_id: UUID, user_id: UUID) -> Claw:
    result = await db.execute(select(Claw).where(Claw.id == claw_id))
    claw = result.scalar_one_or_none()
    if not claw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claw not found")
    if claw.owner_id != user_id:
        result2 = await db.execute(
            select(ClawPermission).where(
                ClawPermission.claw_id == claw_id,
                ClawPermission.user_id == user_id,
                ClawPermission.role == PermissionRole.OWNER,
            )
        )
        if not result2.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners can manage permissions",
            )
    return claw


# ---------------------------------------------------------------------------
# Permissions endpoints
# ---------------------------------------------------------------------------


@router.get("/{claw_id}/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    claw_id: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> list[ClawPermission]:
    await _require_owner(db, claw_id, current_user_id)
    result = await db.execute(
        select(ClawPermission).where(ClawPermission.claw_id == claw_id)
    )
    return list(result.scalars().all())


@router.post(
    "/{claw_id}/permissions",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_permission(
    claw_id: UUID,
    body: AddPermissionRequest,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> ClawPermission:
    await _require_owner(db, claw_id, current_user_id)

    # Validate target user exists
    result = await db.execute(select(User).where(User.id == body.user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if permission already exists
    result2 = await db.execute(
        select(ClawPermission).where(
            ClawPermission.claw_id == claw_id,
            ClawPermission.user_id == body.user_id,
        )
    )
    existing = result2.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has a permission on this Claw",
        )

    perm = ClawPermission(
        claw_id=claw_id,
        user_id=body.user_id,
        role=body.role,
        granted_by=current_user_id,
    )
    db.add(perm)

    # Audit
    db.add(
        AuditLog(
            claw_id=claw_id,
            actor_id=current_user_id,
            action="permission.grant",
            description=f"Granted {body.role} to user {body.user_id}",
            context={"user_id": str(body.user_id), "role": body.role},
        )
    )

    await db.flush()
    await db.refresh(perm)
    return perm


@router.patch("/{claw_id}/permissions/{uid}", response_model=PermissionResponse)
async def update_permission(
    claw_id: UUID,
    uid: UUID,
    body: UpdatePermissionRequest,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> ClawPermission:
    await _require_owner(db, claw_id, current_user_id)

    result = await db.execute(
        select(ClawPermission).where(
            ClawPermission.claw_id == claw_id,
            ClawPermission.user_id == uid,
        )
    )
    perm = result.scalar_one_or_none()
    if not perm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found"
        )

    old_role = perm.role
    perm.role = body.role

    db.add(
        AuditLog(
            claw_id=claw_id,
            actor_id=current_user_id,
            action="permission.update",
            description=f"Changed role for user {uid}: {old_role} → {body.role}",
            context={"user_id": str(uid), "old_role": old_role, "new_role": body.role},
        )
    )

    await db.flush()
    await db.refresh(perm)
    return perm


@router.delete("/{claw_id}/permissions/{uid}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_permission(
    claw_id: UUID,
    uid: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> None:
    await _require_owner(db, claw_id, current_user_id)

    result = await db.execute(
        select(ClawPermission).where(
            ClawPermission.claw_id == claw_id,
            ClawPermission.user_id == uid,
        )
    )
    perm = result.scalar_one_or_none()
    if not perm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found"
        )
    if perm.role == PermissionRole.OWNER and uid == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own owner permission",
        )

    await db.delete(perm)


# ---------------------------------------------------------------------------
# Policy endpoints
# ---------------------------------------------------------------------------


@router.get("/{claw_id}/policies", response_model=PolicyResponse)
async def get_policy(
    claw_id: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> ClawPolicy:
    await _require_owner(db, claw_id, current_user_id)

    result = await db.execute(
        select(ClawPolicy).where(ClawPolicy.claw_id == claw_id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
        )
    return policy


@router.put("/{claw_id}/policies", response_model=PolicyResponse)
async def update_policy(
    claw_id: UUID,
    body: UpdatePolicyRequest,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> ClawPolicy:
    await _require_owner(db, claw_id, current_user_id)

    result = await db.execute(
        select(ClawPolicy).where(ClawPolicy.claw_id == claw_id)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        policy = ClawPolicy(claw_id=claw_id)
        db.add(policy)

    if body.network_policy is not None:
        policy.network_policy = body.network_policy
    if body.fs_policy is not None:
        policy.fs_policy = body.fs_policy
    if body.command_blacklist is not None:
        policy.command_blacklist = body.command_blacklist

    db.add(
        AuditLog(
            claw_id=claw_id,
            actor_id=current_user_id,
            action="policy.update",
            description="Updated Claw resource policy",
            context=body.model_dump(exclude_none=True),
        )
    )

    await db.flush()
    await db.refresh(policy)
    return policy


# ---------------------------------------------------------------------------
# Audit log endpoint
# ---------------------------------------------------------------------------


@router.get("/{claw_id}/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    claw_id: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
    limit: int = 50,
) -> list[AuditLog]:
    await _require_owner(db, claw_id, current_user_id)

    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.claw_id == claw_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())