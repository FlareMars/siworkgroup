"""Claw management API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.core.deps import CurrentUserID, DBSession
from app.models.claw import Claw, ClawStatus
from app.models.permission import ClawPermission, ClawPolicy, PermissionRole

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class SandboxConfigSchema(BaseModel):
    cpu_limit: str = "1.0"
    memory_limit: str = "2g"
    disk_quota: str = "10g"
    network_policy: dict = Field(
        default_factory=lambda: {
            "egress_whitelist": [],
            "allow_localhost": True,
        }
    )
    fs_policy: dict = Field(
        default_factory=lambda: {
            "writable_paths": ["/workspace"],
            "readonly_paths": ["/etc", "/usr"],
            "blocked_paths": ["/proc/sys"],
        }
    )


class CreateClawRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    model: str = "gpt-4o"
    system_prompt: str | None = None
    work_dir: str = "/workspace"
    sandbox_config: SandboxConfigSchema = Field(default_factory=SandboxConfigSchema)
    enabled_tools: list[str] = Field(default_factory=list)


class UpdateClawRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    work_dir: str | None = None
    enabled_tools: list[str] | None = None


class ClawResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    slug: str
    status: ClawStatus
    owner_id: UUID
    container_id: str | None
    model: str
    system_prompt: str | None
    work_dir: str
    sandbox_config: dict
    enabled_tools: list
    created_at: str
    updated_at: str
    last_active_at: str | None

    model_config = {"from_attributes": True}

    def model_post_init(self, __context) -> None:
        # Convert datetimes to ISO strings
        if hasattr(self, "created_at") and not isinstance(self.created_at, str):
            object.__setattr__(self, "created_at", self.created_at.isoformat())
        if hasattr(self, "updated_at") and not isinstance(self.updated_at, str):
            object.__setattr__(self, "updated_at", self.updated_at.isoformat())
        if (
            hasattr(self, "last_active_at")
            and self.last_active_at is not None
            and not isinstance(self.last_active_at, str)
        ):
            object.__setattr__(self, "last_active_at", self.last_active_at.isoformat())


class ClawListResponse(BaseModel):
    items: list[ClawResponse]
    total: int
    page: int
    page_size: int


class StatsResponse(BaseModel):
    container_id: str | None
    status: str
    cpu_percent: float
    memory_usage_mb: float
    memory_limit_mb: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_slug(name: str, existing_slugs: set[str]) -> str:
    """Generate a unique slug from a Claw name."""
    from slugify import slugify
    import secrets

    base = slugify(name)[:100] or "claw"
    slug = base
    counter = 1
    while slug in existing_slugs:
        slug = f"{base}-{secrets.token_hex(3)}"
        counter += 1
    return slug


async def _get_claw_or_404(db: DBSession, claw_id: UUID) -> Claw:
    result = await db.execute(select(Claw).where(Claw.id == claw_id))
    claw = result.scalar_one_or_none()
    if not claw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claw not found")
    return claw


async def _require_role(
    db: DBSession,
    claw_id: UUID,
    user_id: UUID,
    *required_roles: PermissionRole,
) -> None:
    """Assert that user has one of the required roles on the claw, or is owner."""
    result = await db.execute(
        select(ClawPermission).where(
            ClawPermission.claw_id == claw_id,
            ClawPermission.user_id == user_id,
        )
    )
    perm = result.scalar_one_or_none()
    if not perm or perm.role not in required_roles:
        # Also allow if user is the owner (check claw directly)
        claw = await _get_claw_or_404(db, claw_id)
        if claw.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=ClawListResponse)
async def list_claws(
    current_user_id: CurrentUserID,
    db: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: ClawStatus | None = Query(None, alias="status"),
) -> dict:
    """List all Claws accessible by the current user."""
    # Get claw IDs the user has access to (owned or has permission)
    owned_q = select(Claw.id).where(Claw.owner_id == current_user_id)
    perm_q = select(ClawPermission.claw_id).where(
        ClawPermission.user_id == current_user_id
    )

    query = select(Claw).where(
        (Claw.id.in_(owned_q)) | (Claw.id.in_(perm_q))
    )
    if status_filter:
        query = query.where(Claw.status == status_filter)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(Claw.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    claws = result.scalars().all()

    return {
        "items": [ClawResponse.model_validate(c) for c in claws],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=ClawResponse, status_code=status.HTTP_201_CREATED)
async def create_claw(
    body: CreateClawRequest,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> Claw:
    """Create a new Claw instance."""
    # Generate unique slug
    existing = await db.execute(select(Claw.slug))
    existing_slugs = set(existing.scalars().all())
    slug = _make_slug(body.name, existing_slugs)

    claw = Claw(
        name=body.name,
        description=body.description,
        slug=slug,
        owner_id=current_user_id,
        model=body.model,
        system_prompt=body.system_prompt,
        work_dir=body.work_dir,
        sandbox_config=body.sandbox_config.model_dump(),
        enabled_tools=body.enabled_tools,
    )
    db.add(claw)
    await db.flush()

    # Create default policy
    policy = ClawPolicy(claw_id=claw.id)
    db.add(policy)

    # Grant owner permission
    owner_perm = ClawPermission(
        claw_id=claw.id,
        user_id=current_user_id,
        role=PermissionRole.OWNER,
        granted_by=current_user_id,
    )
    db.add(owner_perm)

    await db.flush()
    await db.refresh(claw)
    return claw


@router.get("/{claw_id}", response_model=ClawResponse)
async def get_claw(
    claw_id: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> Claw:
    """Get Claw details."""
    claw = await _get_claw_or_404(db, claw_id)
    await _require_role(
        db, claw_id, current_user_id,
        PermissionRole.OWNER, PermissionRole.COLLABORATOR, PermissionRole.VIEWER,
    )
    return claw


@router.patch("/{claw_id}", response_model=ClawResponse)
async def update_claw(
    claw_id: UUID,
    body: UpdateClawRequest,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> Claw:
    """Update Claw configuration."""
    claw = await _get_claw_or_404(db, claw_id)
    await _require_role(db, claw_id, current_user_id, PermissionRole.OWNER)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(claw, field, value)

    await db.flush()
    await db.refresh(claw)
    return claw


@router.delete("/{claw_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claw(
    claw_id: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> None:
    """Delete a Claw and cascade clean up all related resources."""
    claw = await _get_claw_or_404(db, claw_id)
    await _require_role(db, claw_id, current_user_id, PermissionRole.OWNER)

    await db.delete(claw)


@router.post("/{claw_id}/start", response_model=ClawResponse)
async def start_claw(
    claw_id: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> Claw:
    """Start a stopped/pending Claw container."""
    claw = await _get_claw_or_404(db, claw_id)
    await _require_role(db, claw_id, current_user_id, PermissionRole.OWNER)

    if claw.status == ClawStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Claw is already running"
        )

    # TODO: Integrate with sandbox_service to start Docker container
    claw.status = ClawStatus.RUNNING
    await db.flush()
    await db.refresh(claw)
    return claw


@router.post("/{claw_id}/stop", response_model=ClawResponse)
async def stop_claw(
    claw_id: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> Claw:
    """Stop a running Claw container."""
    claw = await _get_claw_or_404(db, claw_id)
    await _require_role(db, claw_id, current_user_id, PermissionRole.OWNER)

    if claw.status != ClawStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Claw is not running"
        )

    # TODO: Integrate with sandbox_service to stop Docker container
    claw.status = ClawStatus.STOPPED
    await db.flush()
    await db.refresh(claw)
    return claw


@router.get("/{claw_id}/stats", response_model=StatsResponse)
async def get_claw_stats(
    claw_id: UUID,
    current_user_id: CurrentUserID,
    db: DBSession,
) -> dict:
    """Get real-time resource usage statistics for a Claw."""
    claw = await _get_claw_or_404(db, claw_id)
    await _require_role(
        db, claw_id, current_user_id,
        PermissionRole.OWNER, PermissionRole.COLLABORATOR, PermissionRole.VIEWER,
    )

    # TODO: Fetch real stats from Docker SDK via sandbox_service
    return {
        "container_id": claw.container_id,
        "status": claw.status,
        "cpu_percent": 0.0,
        "memory_usage_mb": 0.0,
        "memory_limit_mb": 2048.0,
    }