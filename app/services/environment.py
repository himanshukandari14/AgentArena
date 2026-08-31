"""
EnvironmentManager — Real Docker-per-run isolation.

Each task run gets a fresh container from the agentforge-sandbox image.
The container:
  - Starts with a baked-in seeded SQLite snapshot (no shared state)
  - Exposes the MCP SSE server on a random host port
  - Is CPU/memory limited
  - Is forcibly destroyed after the run (pass, fail, or timeout)
"""

import logging
import os
import socket
import time
import urllib.request
import urllib.error

import docker
import docker.errors

logger = logging.getLogger(__name__)

SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "agentforge-sandbox:latest")
MCP_CONTAINER_PORT = 9000  # port the MCP SSE server listens on inside the container


def _find_free_port() -> int:
    """Find an available TCP port on the host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


class EnvironmentManager:
    """
    Manages isolated Docker task run environments.

    Lifecycle:
      prepare_isolated_environment() → spawns container, returns (container_id, mcp_url, env_version)
      cleanup_environment()          → stops + removes container unconditionally
    """

    @staticmethod
    def prepare_isolated_environment(
        timeout_seconds: int = 60,
    ) -> tuple[str, str, str]:
        """
        Spawn a fresh sandbox container.

        Returns:
            (container_id, mcp_url, env_version)
            mcp_url is the HTTP SSE endpoint the agent runner should connect to.

        Raises:
            RuntimeError if the container fails to start or the MCP server
            does not become reachable within the startup grace period.
        """
        env_version = os.getenv("ENV_VERSION", "v1.0.0")
        client = docker.from_env()

        host_port = _find_free_port()

        # Resource limits per project guide §15
        container = client.containers.run(
            image=SANDBOX_IMAGE,
            detach=True,
            remove=False,           # we remove explicitly in cleanup so we can inspect on failure
            ports={f"{MCP_CONTAINER_PORT}/tcp": host_port},
            nano_cpus=int(1.0 * 1e9),   # 1 CPU
            mem_limit="512m",
            network_mode="bridge",
            environment={
                "DATABASE_URL": "sqlite:////app/agentdesk.db",
                "ENV_VERSION": env_version,
                "MCP_PORT": str(MCP_CONTAINER_PORT),
            },
        )

        container_id = container.id[:12]
        mcp_url = f"http://localhost:{host_port}/sse"

        logger.info(
            f"Spawned sandbox container {container_id} "
            f"(image={SANDBOX_IMAGE}, host_port={host_port}, env={env_version})"
        )

        # Wait until Uvicorn is actually serving /sse (not just TCP open).
        # The container runs `uv sync` on startup which takes ~10-15s before
        # Uvicorn binds — bare TCP would succeed too early.
        _wait_for_sse("localhost", host_port, timeout=60)

        return container_id, mcp_url, env_version

    @staticmethod
    def cleanup_environment(container_id: str) -> None:
        """
        Stop and remove the container unconditionally.
        Called in finally blocks so it runs even on crashes/timeouts.
        """
        if not container_id:
            return
        try:
            client = docker.from_env()
            # Use full ID prefix lookup
            containers = client.containers.list(all=True, filters={"id": container_id})
            if not containers:
                logger.warning(f"Container {container_id} not found during cleanup (may have already exited)")
                return
            container = containers[0]
            try:
                container.stop(timeout=5)
            except Exception:
                pass  # already stopped
            container.remove(force=True)
            logger.info(f"Destroyed sandbox container {container_id}")
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} already removed")
        except Exception as e:
            logger.error(f"Failed to cleanup container {container_id}: {e}")


def _wait_for_sse(host: str, port: int, timeout: int = 60) -> None:
    """
    Poll the /sse HTTP endpoint until it returns HTTP 200.

    This is more reliable than a bare TCP check because the sandbox container
    runs `uv sync` at startup (~10-15s) before Uvicorn binds. A TCP check
    would succeed as soon as the port is open but before the SSE server is ready.
    """
    url = f"http://{host}:{port}/sse"
    deadline = time.monotonic() + timeout
    last_err = None
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception as e:
            last_err = e
            time.sleep(1)
    raise RuntimeError(
        f"MCP SSE server at {url} did not become ready within {timeout}s. "
        f"Last error: {last_err}. "
        "Check that the sandbox image is built and the MCP server starts correctly."
    )
