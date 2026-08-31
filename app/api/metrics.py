import math
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import TaskRun

router = APIRouter(prefix="", tags=["metrics"])


@router.get("/metrics")
def get_system_metrics(db: Session = Depends(get_db)):
    """
    Returns system evaluation metrics:
    - total runs & active runs
    - success rate % & average score
    - P95 execution runtime latency
    - failure category distribution (MODEL, ENVIRONMENT, TASK)
    """
    runs = db.scalars(select(TaskRun)).all()

    total_runs = len(runs)
    if total_runs == 0:
        return {
            "total_runs": 0,
            "active_runs": 0,
            "passed_runs": 0,
            "failed_runs": 0,
            "success_rate_percent": 0.0,
            "avg_score": 0.0,
            "avg_runtime_seconds": 0.0,
            "p95_runtime_seconds": 0.0,
            "failure_breakdown": {
                "MODEL_FAILURE": 0,
                "ENVIRONMENT_FAILURE": 0,
                "TASK_FAILURE": 0,
                "NONE": 0,
            },
        }

    active_runs = sum(1 for r in runs if r.status in ["queued", "running"])
    passed_runs = sum(1 for r in runs if r.status == "passed")
    failed_runs = sum(1 for r in runs if r.status in ["failed", "timed_out"])

    success_rate = round((passed_runs / total_runs) * 100, 1)
    avg_score = round(sum(r.score for r in runs) / total_runs, 2)

    runtimes = sorted([r.duration_seconds for r in runs if r.duration_seconds is not None])

    avg_runtime = round(sum(runtimes) / len(runtimes), 2) if runtimes else 0.0

    if runtimes:
        p95_idx = math.ceil(0.95 * len(runtimes)) - 1
        p95_runtime = round(runtimes[max(0, p95_idx)], 2)
    else:
        p95_runtime = 0.0

    failure_breakdown = {
        "MODEL_FAILURE": sum(1 for r in runs if r.failure_category == "MODEL_FAILURE"),
        "ENVIRONMENT_FAILURE": sum(1 for r in runs if r.failure_category == "ENVIRONMENT_FAILURE"),
        "TASK_FAILURE": sum(1 for r in runs if r.failure_category == "TASK_FAILURE"),
        "NONE": sum(1 for r in runs if r.failure_category == "NONE"),
    }

    return {
        "total_runs": total_runs,
        "active_runs": active_runs,
        "passed_runs": passed_runs,
        "failed_runs": failed_runs,
        "success_rate_percent": success_rate,
        "avg_score": avg_score,
        "avg_runtime_seconds": avg_runtime,
        "p95_runtime_seconds": p95_runtime,
        "failure_breakdown": failure_breakdown,
    }
