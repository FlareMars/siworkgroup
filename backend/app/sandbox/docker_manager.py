"""Docker container manager for Claw sandboxes."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DockerManager:
    """Manages Docker containers for Claw sandbox instances."""

    def __init__(self) -> None:
        self._client: docker.DockerClient | None = None

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            self._client = docker.DockerClient(base_url=settings.DOCKER_HOST)
        return self._client

    def _container_name(self, claw_id: UUID) -> str:
        return f"claw-{claw_id}"

    async def create_container(
        self,
        claw_id: UUID,
        sandbox_config: dict[str, Any],
    ) -> str:
        """Create a new sandbox container for a Claw. Returns the container ID."""
        name = self._container_name(claw_id)
        cpu_limit = float(sandbox_config.get("cpu_limit", settings.SANDBOX_CPU_DEFAULT))
        memory_limit = sandbox_config.get("memory_limit", settings.SANDBOX_MEMORY_DEFAULT)
        work_dir = sandbox_config.get("work_dir", "/workspace")

        loop = asyncio.get_event_loop()

        def _create() -> Container:
            return self.client.containers.create(
                image=settings.SANDBOX_IMAGE,
                name=name,
                detach=True,
                tty=True,
                stdin_open=True,
                working_dir=work_dir,
                cpu_period=100_000,
                cpu_quota=int(cpu_limit * 100_000),
                mem_limit=memory_limit,
                network=settings.SANDBOX_NETWORK,
                security_opt=["no-new-privileges:true"],
                labels={"siworkgroup.claw_id": str(claw_id)},
                environment={
                    "CLAW_ID": str(claw_id),
                    "WORKSPACE": work_dir,
                },
            )

        try:
            container = await loop.run_in_executor(None, _create)
            logger.info("Created container", claw_id=str(claw_id), container_id=container.id)
            return container.id
        except DockerException as exc:
            logger.error("Failed to create container", claw_id=str(claw_id), error=str(exc))
            raise

    async def start_container(self, container_id: str) -> None:
        """Start an existing container."""
        loop = asyncio.get_event_loop()

        def _start() -> None:
            container = self.client.containers.get(container_id)
            container.start()

        await loop.run_in_executor(None, _start)
        logger.info("Started container", container_id=container_id)

    async def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """Stop a running container gracefully."""
        loop = asyncio.get_event_loop()

        def _stop() -> None:
            try:
                container = self.client.containers.get(container_id)
                container.stop(timeout=timeout)
            except NotFound:
                pass

        await loop.run_in_executor(None, _stop)
        logger.info("Stopped container", container_id=container_id)

    async def remove_container(self, container_id: str, force: bool = True) -> None:
        """Remove a container."""
        loop = asyncio.get_event_loop()

        def _remove() -> None:
            try:
                container = self.client.containers.get(container_id)
                container.remove(force=force)
            except NotFound:
                pass

        await loop.run_in_executor(None, _remove)
        logger.info("Removed container", container_id=container_id)

    async def get_stats(self, container_id: str) -> dict[str, Any]:
        """Get resource usage statistics for a running container."""
        loop = asyncio.get_event_loop()

        def _stats() -> dict:
            container = self.client.containers.get(container_id)
            return container.stats(stream=False)

        raw = await loop.run_in_executor(None, _stats)

        # Parse CPU usage
        cpu_delta = (
            raw["cpu_stats"]["cpu_usage"]["total_usage"]
            - raw["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        system_delta = (
            raw["cpu_stats"]["system_cpu_usage"]
            - raw["precpu_stats"]["system_cpu_usage"]
        )
        num_cpus = raw["cpu_stats"].get("online_cpus", 1)
        cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0 if system_delta > 0 else 0.0

        # Parse memory usage
        mem_usage = raw["memory_stats"]["usage"] / (1024 * 1024)  # bytes -> MB
        mem_limit = raw["memory_stats"]["limit"] / (1024 * 1024)

        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_usage_mb": round(mem_usage, 2),
            "memory_limit_mb": round(mem_limit, 2),
        }

    async def exec_command(
        self,
        container_id: str,
        command: str | list[str],
        workdir: str = "/workspace",
    ) -> tuple[int, str]:
        """Execute a command inside a container. Returns (exit_code, output)."""
        loop = asyncio.get_event_loop()

        def _exec() -> tuple[int, str]:
            container = self.client.containers.get(container_id)
            result = container.exec_run(
                command,
                workdir=workdir,
                demux=False,
            )
            output = result.output.decode("utf-8", errors="replace") if result.output else ""
            return result.exit_code, output

        return await loop.run_in_executor(None, _exec)

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None


# Singleton instance
docker_manager = DockerManager()