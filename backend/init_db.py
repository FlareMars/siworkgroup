"""Initialize database tables and stamp alembic version."""
import asyncio
import sys

sys.path.insert(0, ".")


async def main():
    result_lines = []
    try:
        from app.core.config import settings
        result_lines.append(f"Config loaded: {settings.APP_NAME}")
        result_lines.append(f"DB URL: {settings.DATABASE_URL[:60]}...")

        from app.core.database import Base, engine
        from app.models import (  # noqa: F401
            AuditLog,
            Claw,
            ClawPermission,
            ClawPolicy,
            ChatSession,
            ChatMessage,
            User,
        )

        result_lines.append(f"Models registered: {list(Base.metadata.tables.keys())}")

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        result_lines.append("SUCCESS: All tables created")
        await engine.dispose()

    except Exception as e:
        import traceback
        result_lines.append(f"ERROR: {e}")
        result_lines.append(traceback.format_exc())

    output = "\n".join(result_lines)
    with open("init_db_result.txt", "w") as f:
        f.write(output)
    print(output)


if __name__ == "__main__":
    asyncio.run(main())