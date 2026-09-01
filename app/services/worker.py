"""
Task run orchestrator.

Flow:
  1. Load task definition
  2. Spawn isolated Docker container (EnvironmentManager)
  3. Run AI agent via MCP SSE endpoint inside the container
  4. Log all tool calls
  5. Evaluate outcome with verifier + failure attribution
  6. Persist result to DB
  7. Destroy container unconditionally (finally block)

Timeout: if the agent exceeds task.timeout_seconds the run is cancelled
and the container is force-killed.
"""

import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import SessionLocal
from app.models import TaskRun, ToolCallRecord
from app.tasks.definitions import get_task
from app.services.evaluator import evaluate_task_run
from app.agent.runner import run_agent_for_task
from app.services.environment import EnvironmentManager
from app.telemetry import get_tracer

logger = logging.getLogger(__name__)


def create_task_run(db: Session, task_id: str) -> TaskRun:
    """Create a new TaskRun record in queued state."""
    get_task(task_id)  # validates task_id exists

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    task_run = TaskRun(
        id=run_id,
        task_id=task_id,
        status="queued",
        start_time=datetime.now(timezone.utc),
    )
    db.add(task_run)
    db.commit()
    db.refresh(task_run)
    return task_run


async def execute_task_run_async(run_id: str) -> dict:
    """
    Executes a queued task run asynchronously inside an isolated Docker container.

    Steps:
      1. Provisions a fresh Docker sandbox (agentarena-sandbox image)
      2. Connects agent to MCP SSE server running inside the container
      3. Agent performs tool calls against the container's isolated SQLite DB
      4. Verifier inspects the container's final DB state
      5. Container is destroyed (pass/fail/crash/timeout)
    """
    tracer = get_tracer()
    db = SessionLocal()
    container_id: str | None = None

    try:
        task_run = db.get(TaskRun, run_id)
        if not task_run:
            raise ValueError(f"Run ID {run_id} not found.")

        task_def = get_task(task_run.task_id)

        task_run.status = "running"
        task_run.start_time = datetime.now(timezone.utc)
        db.commit()

        with tracer.start_as_current_span(
            "agentarena.task_run",
            attributes={
                "run_id": run_id,
                "task_id": task_def.id,
                "difficulty": task_def.difficulty,
            },
        ) as span:

            # ── 1. Provision isolated Docker environment ────────────────────
            with tracer.start_as_current_span("agentarena.environment_prepare"):
                container_id, mcp_url, env_version = (
                    EnvironmentManager.prepare_isolated_environment(
                        timeout_seconds=task_def.timeout_seconds,
                    )
                )

            task_run.container_id = container_id
            task_run.env_version = env_version
            db.commit()

            logger.info(
                f"[{run_id}] Container {container_id} ready — "
                f"MCP at {mcp_url} — timeout={task_def.timeout_seconds}s"
            )

            # ── 2. Run agent (with task-level timeout) ─────────────────────
            start_ts = datetime.now(timezone.utc)

            with tracer.start_as_current_span("agentarena.agent_execution"):
                try:
                    agent_result = await asyncio.wait_for(
                        run_agent_for_task(
                            task_description=task_def.description,
                            mcp_url=mcp_url,
                        ),
                        timeout=task_def.timeout_seconds,
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"[{run_id}] Task timed out after {task_def.timeout_seconds}s")
                    task_run.status = "timed_out"
                    task_run.failure_category = "ENVIRONMENT_FAILURE"
                    task_run.failure_reason = f"Agent exceeded timeout of {task_def.timeout_seconds}s"
                    task_run.end_time = datetime.now(timezone.utc)
                    task_run.duration_seconds = round(
                        (task_run.end_time - start_ts).total_seconds(), 2
                    )
                    db.commit()
                    return {
                        "run_id": run_id,
                        "status": "timed_out",
                        "score": 0.0,
                        "failure_category": "ENVIRONMENT_FAILURE",
                        "failure_reason": task_run.failure_reason,
                        "duration_seconds": task_run.duration_seconds,
                    }

            end_ts = datetime.now(timezone.utc)
            duration = (end_ts - start_ts).total_seconds()

            # ── 3. Persist tool call logs ───────────────────────────────────
            tool_calls_data = agent_result.get("tool_calls", [])
            tool_error_count = 0

            for step_idx, call in enumerate(tool_calls_data, start=1):
                if not call.get("success", True):
                    tool_error_count += 1
                record = ToolCallRecord(
                    run_id=run_id,
                    step=step_idx,
                    tool_name=call.get("name", "unknown"),
                    arguments_json=json.dumps(call.get("arguments", {}), default=str),
                    result_json=json.dumps(call.get("result", {}), default=str),
                )
                db.add(record)

            # ── 4. Copy container DB → host, run verifier against real state ─
            # The container's SQLite has the agent's changes. The host DB does
            # not. We must copy before destroying the container.
            with tracer.start_as_current_span("agentarena.verifier_eval"):
                verifier_db_session = None
                tmp_db_path = None
                try:
                    tmp_fd, tmp_db_path = tempfile.mkstemp(suffix=".db", prefix=f"agentarena_{run_id}_")
                    os.close(tmp_fd)

                    EnvironmentManager.copy_db_from_container(container_id, tmp_db_path)

                    # Open a fresh SQLAlchemy session against the container's DB copy
                    tmp_engine = create_engine(
                        f"sqlite:///{tmp_db_path}",
                        connect_args={"check_same_thread": False},
                    )
                    TmpSession = sessionmaker(bind=tmp_engine)
                    verifier_db_session = TmpSession()

                    evaluation = evaluate_task_run(
                        db=verifier_db_session,
                        task_def=task_def,
                        executed_steps=len(tool_calls_data),
                        tool_error_count=tool_error_count,
                        agent_error=agent_result.get("error"),
                    )
                finally:
                    if verifier_db_session:
                        verifier_db_session.close()
                    if tmp_db_path and os.path.exists(tmp_db_path):
                        os.unlink(tmp_db_path)
                        logger.debug(f"Removed temp verifier DB {tmp_db_path}")

            task_run.end_time = end_ts
            task_run.duration_seconds = round(duration, 2)
            task_run.status = "passed" if evaluation["passed"] else "failed"
            task_run.score = evaluation["score"]
            task_run.failure_category = evaluation["failure_category"]
            task_run.failure_reason = evaluation["failure_reason"]
            task_run.agent_output = agent_result.get("output_text", "")

            span.set_attribute("status", task_run.status)
            span.set_attribute("score", task_run.score)
            span.set_attribute("container_id", container_id or "")
            span.set_attribute("env_version", env_version)
            span.set_attribute("failure_category", task_run.failure_category)
            span.set_attribute("duration_seconds", task_run.duration_seconds)

            db.commit()
            db.refresh(task_run)

            logger.info(
                f"[{run_id}] Completed — status={task_run.status} "
                f"score={task_run.score} container={container_id}"
            )

            return {
                "run_id": run_id,
                "status": task_run.status,
                "score": task_run.score,
                "failure_category": task_run.failure_category,
                "failure_reason": task_run.failure_reason,
                "duration_seconds": task_run.duration_seconds,
                "container_id": container_id,
                "env_version": env_version,
            }

    except Exception as e:
        logger.error(f"[{run_id}] Worker exception: {e}", exc_info=True)
        task_run = db.get(TaskRun, run_id)
        if task_run:
            task_run.status = "failed"
            task_run.failure_category = "ENVIRONMENT_FAILURE"
            task_run.failure_reason = f"Worker runner exception: {str(e)}"
            task_run.end_time = datetime.now(timezone.utc)
            if container_id:
                task_run.container_id = container_id
            db.commit()
        raise e

    finally:
        db.close()
        # ── 5. Destroy container unconditionally ───────────────────────────
        if container_id:
            EnvironmentManager.cleanup_environment(container_id)
