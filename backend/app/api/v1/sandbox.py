"""Sandbox configuration API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.core.deps import CurrentUserID, DBSession
from app.models.claw import Claw
from app.models.permission import ClawPermission, PermissionRole

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class SandboxResponse(BaseModel):
    cpu_limit: str
    memory_limit: str
    disk_quota: str
    network_policy: dict
    fs_policy: dict


class UpdateSandboxRequest(BaseModel):
    cpu_limit: str | None = None
    memory_limit: str | None = None
    disk_quota: str | None = None
    network_policy: dict | None = None
    fs_policy: dict | None = None


class FilesystemEntry(BaseModel):
    name: str
    path: str
    type: str  # "file" | "directory"
    size: int | None = None
    modified_at: str | None = None


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
                detail="Only owners can manage sandbox configuration",
            )
    return claw


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/{claw_id}/sandbox", response_model=SandboxResponse)
async def get_sandbox(
    claw_id: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> dict:
    """Get sandbox configuration for a Claw."""
    claw = await _require_owner(db, claw_id, current_user_id)
    config = claw.sandbox_config or {}

    return {
        "cpu_limit": config.get("cpu_limit", "1.0"),
        "memory_limit": config.get("memory_limit", "2g"),
        "disk_quota": config.get("disk_quota", "10g"),
        "network_policy": config.get(
            "network_policy", {"egress_whitelist": [], "allow_localhost": True}
        ),
        "fs_policy": config.get(
            "fs_policy",
            {
                "writable_paths": ["/workspace"],
                "readonly_paths": ["/etc", "/usr"],
                "blocked_paths": ["/proc/sys"],
            },
        ),
    }


@router.put("/{claw_id}/sandbox", response_model=SandboxResponse)
async def update_sandbox(
    claw_id: UUID,
    body: UpdateSandboxRequest,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> dict:
    """Update sandbox configuration for a Claw."""
    claw = await _require_owner(db, claw_id, current_user_id)

    config = dict(claw.sandbox_config or {})
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            config[field] = value

    claw.sandbox_config = config
    await db.flush()

    return {
        "cpu_limit": config.get("cpu_limit", "1.0"),
        "memory_limit": config.get("memory_limit", "2g"),
        "disk_quota": config.get("disk_quota", "10g"),
        "network_policy": config.get("network_policy", {}),
        "fs_policy": config.get("fs_policy", {}),
    }


@router.post("/{claw_id}/sandbox/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_sandbox(
    claw_id: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> None:
    """Reset the sandbox environment (destroys and recreates the container)."""
    claw = await _require_owner(db, claw_id, current_user_id)

    from app.models.claw import ClawStatus

    if claw.status == ClawStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stop the Claw before resetting its sandbox",
        )

    # TODO: Integrate with sandbox_service to destroy and recreate container
    claw.container_id = None
    claw.container_name = None
    await db.flush()


@router.get("/{claw_id}/sandbox/filesystem", response_model=list[FilesystemEntry])
async def browse_filesystem(
    claw_id: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
    path: str = "/workspace",
) -> list[dict]:
    """Browse the sandbox filesystem."""
    result = await db.execute(select(Claw).where(Claw.id == claw_id))
    claw = result.scalar_one_or_none()
    if not claw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claw not found")

    from app.models.claw import ClawStatus

    if claw.status != ClawStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Claw must be running to browse filesystem",
        )

    # TODO: Integrate with sandbox_service to list container files
    return []