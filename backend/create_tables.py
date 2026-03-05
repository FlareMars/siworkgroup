"""One-time script to create all database tables using SQLAlchemy metadata."""
import asyncio
import sys

sys.path.insert(0, ".")


async def main():
    from app.core.database import Base, engine
    # Import all models to ensure they're registered with Base.metadata
    from app.models import (  # noqa: F401
        AuditLog,
        Claw,
        ClawPermission,
        ClawPolicy,
        ChatSession,
        ChatMessage,
        User,
    )

    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("All tables created successfully!")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())