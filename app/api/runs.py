from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import TaskRun, ToolCallRecord
from app.tasks.definitions import list_tasks, get_task
from app.services.worker import create_task_run, execute_task_run_async

router = APIRouter(prefix="", tags=["runs"])


class CreateRunRequest(BaseModel):
    task_id: str


class TaskRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    status: str
    score: float
    failure_category: str
    failure_reason: str | None
    duration_seconds: float | None
    start_time: str | None
    end_time: str | None


@router.get("/tasks")
def get_available_tasks():
    """List all available task definitions in the suite."""
    return {"tasks": list_tasks()}


@router.post("/runs", status_code=status.HTTP_202_ACCEPTED)
async def trigger_run(
    payload: CreateRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger an asynchronous task run environment."""
    try:
        task_run = create_task_run(db, payload.task_id)
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))

    # Queue execution worker in background
    background_tasks.add_task(execute_task_run_async, task_run.id)

    return {
        "run_id": task_run.id,
        "task_id": task_run.task_id,
        "status": task_run.status,
        "message": "Task run queued successfully.",
    }


@router.get("/runs")
def list_runs(db: Session = Depends(get_db)):
    """List all historical task runs."""
    runs = db.scalars(select(TaskRun).order_by(TaskRun.start_time.desc())).all()
    return [
        {
            "id": r.id,
            "task_id": r.task_id,
            "status": r.status,
            "score": r.score,
            "failure_category": r.failure_category,
            "failure_reason": r.failure_reason,
            "duration_seconds": r.duration_seconds,
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "end_time": r.end_time.isoformat() if r.end_time else None,
        }
        for r in runs
    ]


@router.get("/runs/{run_id}")
def get_run_details(run_id: str, db: Session = Depends(get_db)):
    """Get full details and tool call trace for a task run."""
    run = db.get(TaskRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    tool_calls = db.scalars(
        select(ToolCallRecord)
        .where(ToolCallRecord.run_id == run_id)
        .order_by(ToolCallRecord.step.asc())
    ).all()

    return {
        "id": run.id,
        "task_id": run.task_id,
        "status": run.status,
        "score": run.score,
        "failure_category": run.failure_category,
        "failure_reason": run.failure_reason,
        "agent_output": run.agent_output,
        "duration_seconds": run.duration_seconds,
        "start_time": run.start_time.isoformat() if run.start_time else None,
        "end_time": run.end_time.isoformat() if run.end_time else None,
        "tool_call_trace": [
            {
                "step": tc.step,
                "tool_name": tc.tool_name,
                "arguments": tc.arguments_json,
                "result": tc.result_json,
            }
            for tc in tool_calls
        ],
    }


@router.post("/runs/{run_id}/replay", status_code=status.HTTP_202_ACCEPTED)
async def replay_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Replay a previous task run with a fresh environment state."""
    original_run = db.get(TaskRun, run_id)
    if not original_run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    new_run = create_task_run(db, original_run.task_id)
    background_tasks.add_task(execute_task_run_async, new_run.id)

    return {
        "replayed_from": run_id,
        "new_run_id": new_run.id,
        "task_id": new_run.task_id,
        "status": new_run.status,
        "message": f"Replay launched under run_id {new_run.id}.",
    }
