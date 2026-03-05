"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1 import router as api_v1_router
from app.api.ws.chat_ws import router as ws_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    configure_logging()
    logger.info(
        "Starting SiWorkGroup API",
        version=settings.VERSION,
        env=settings.APP_ENV,
    )

    # Validate database connectivity on startup
    try:
        from app.core.database import engine
        async with engine.begin() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info("Database connection established")
    except Exception as exc:
        logger.error("Database connection failed", error=str(exc))

    yield

    logger.info("Shutting down SiWorkGroup API")
    from app.core.database import engine
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="SiWorkGroup API",
        description=(
            "**Si-Worker Inside** — Unified management, permission isolation, "
            "and sandbox-safe OpenClaw agent workgroup platform."
        ),
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )

    # -------------------------------------------------------------------------
    # Middleware
    # -------------------------------------------------------------------------
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------------------------------------------------------
    # Routers
    # -------------------------------------------------------------------------
    app.include_router(api_v1_router)
    app.include_router(ws_router)

    # -------------------------------------------------------------------------
    # Health check
    # -------------------------------------------------------------------------
    @app.get("/health", tags=["Health"], include_in_schema=False)
    async def health_check() -> dict:
        return {"status": "ok", "version": settings.VERSION}

    @app.get("/", tags=["Root"], include_in_schema=False)
    async def root() -> dict:
        return {
            "name": settings.APP_NAME,
            "version": settings.VERSION,
            "docs": "/docs",
        }

    return app


app = create_app()