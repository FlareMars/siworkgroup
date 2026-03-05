"""Celery task definitions."""

from app.worker import celery_app


@celery_app.task(bind=True, name="tasks.start_claw_container")
def start_claw_container(self, claw_id: str) -> dict:
    """Async task: create and start a Claw Docker container."""
    import asyncio
    from uuid import UUID

    from app.core.database import AsyncSessionLocal
    from app.models.claw import Claw, ClawStatus
    from app.sandbox.docker_manager import docker_manager

    async def _run():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select

            result = await db.execute(select(Claw).where(Claw.id == UUID(claw_id)))
            claw = result.scalar_one_or_none()
            if not claw:
                return {"error": f"Claw {claw_id} not found"}

            try:
                container_id = await docker_manager.create_container(
                    claw.id, claw.sandbox_config
                )
                await docker_manager.start_container(container_id)
                claw.container_id = container_id
                claw.container_name = f"claw-{claw_id}"
                claw.status = ClawStatus.RUNNING
                await db.commit()
                return {"container_id": container_id, "status": "running"}
            except Exception as exc:
                claw.status = ClawStatus.ERROR
                await db.commit()
                return {"error": str(exc)}

    return asyncio.run(_run())


@celery_app.task(bind=True, name="tasks.stop_claw_container")
def stop_claw_container(self, claw_id: str, container_id: str) -> dict:
    """Async task: stop and remove a Claw Docker container."""
    import asyncio
    from uuid import UUID

    from app.core.database import AsyncSessionLocal
    from app.models.claw import Claw, ClawStatus
    from app.sandbox.docker_manager import docker_manager

    async def _run():
        await docker_manager.stop_container(container_id)
        await docker_manager.remove_container(container_id)

        async with AsyncSessionLocal() as db:
            from sqlalchemy import select

            result = await db.execute(select(Claw).where(Claw.id == UUID(claw_id)))
            claw = result.scalar_one_or_none()
            if claw:
                claw.status = ClawStatus.STOPPED
                claw.container_id = None
                await db.commit()

        return {"status": "stopped"}

    return asyncio.run(_run())