import asyncio
import json
import logging
from datetime import datetime, timezone
import uuid

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import TaskRun, ToolCallRecord
from app.tasks.definitions import get_task
from app.services.evaluator import evaluate_task_run
from app.agent.runner import run_agent_for_task

logger = logging.getLogger(__name__)


def create_task_run(db: Session, task_id: str) -> TaskRun:
    """Create a new TaskRun record in queued state."""
    # Ensure task exists
    get_task(task_id)

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
    Executes a queued task run asynchronously:
    1. Loads task definition
    2. Runs agent via MCP tool interface
    3. Logs tool calls & duration
    4. Evaluates outcome with verifier & Failure Attribution classifier
    5. Saves result to DB
    """
    db = SessionLocal()
    try:
        task_run = db.get(TaskRun, run_id)
        if not task_run:
            raise ValueError(f"Run ID {run_id} not found.")

        task_run.status = "running"
        task_run.start_time = datetime.now(timezone.utc)
        db.commit()

        task_def = get_task(task_run.task_id)

        start_ts = datetime.now(timezone.utc)
        agent_result = await run_agent_for_task(task_def.description)
        end_ts = datetime.now(timezone.utc)

        duration = (end_ts - start_ts).total_seconds()

        # Save tool call logs
        tool_calls_data = agent_result.get("tool_calls", [])
        tool_error_count = 0

        for step_idx, call in enumerate(tool_calls_data, start=1):
            if not call.get("success", True):
                tool_error_count += 1
            record = ToolCallRecord(
                run_id=run_id,
                step=step_idx,
                tool_name=call.get("name", "unknown"),
                arguments_json=json.dumps(call.get("arguments", {})),
                result_json=json.dumps(call.get("result", {})),
            )
            db.add(record)

        # Run verification and failure attribution
        evaluation = evaluate_task_run(
            db=db,
            task_def=task_def,
            executed_steps=len(tool_calls_data),
            tool_error_count=tool_error_count,
            agent_error=agent_result.get("error"),
        )

        task_run.end_time = end_ts
        task_run.duration_seconds = round(duration, 2)
        task_run.status = "passed" if evaluation["passed"] else "failed"
        task_run.score = evaluation["score"]
        task_run.failure_category = evaluation["failure_category"]
        task_run.failure_reason = evaluation["failure_reason"]
        task_run.agent_output = agent_result.get("output_text", "")

        db.commit()
        db.refresh(task_run)

        return {
            "run_id": run_id,
            "status": task_run.status,
            "score": task_run.score,
            "failure_category": task_run.failure_category,
            "failure_reason": task_run.failure_reason,
            "duration_seconds": task_run.duration_seconds,
        }

    except Exception as e:
        logger.error(f"Error executing run {run_id}: {e}", exc_info=True)
        task_run = db.get(TaskRun, run_id)
        if task_run:
            task_run.status = "failed"
            task_run.failure_category = "ENVIRONMENT_FAILURE"
            task_run.failure_reason = f"Worker runner exception: {str(e)}"
            task_run.end_time = datetime.now(timezone.utc)
            db.commit()
        raise e
    finally:
        db.close()
