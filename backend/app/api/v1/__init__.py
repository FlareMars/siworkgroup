"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1 import auth, chat, claws, permissions, sandbox

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(claws.router, prefix="/claws", tags=["Claws"])
router.include_router(permissions.router, prefix="/claws", tags=["Permissions"])
router.include_router(sandbox.router, prefix="/claws", tags=["Sandbox"])
router.include_router(chat.router, prefix="/claws", tags=["Chat"])