import asyncio
import math
import os
import time

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.worker import create_task_run, execute_task_run_async
from app.tasks.definitions import TASKS


async def benchmark_concurrent_runs(
    concurrency_level: int = 10,
    timeout_multiplier: float = 1.0,
):
    """
    Load Testing & Concurrency Benchmark Engine.

    Executes `concurrency_level` evaluation tasks in parallel inside isolated
    Docker containers and measures p50/p95/p99 latencies and throughput.

    Args:
        concurrency_level: Number of parallel task runs.
        timeout_multiplier: Scale each task's timeout by this factor.
            Use >1 when running concurrent Docker containers — they share CPU
            and LLM round-trips slow down under load, causing false timeouts.
            This was the measured bottleneck at concurrency >= 3.
    """
    print(f"\n==================================================")
    print(f" AGENTARENA CONCURRENCY BENCHMARK (N={concurrency_level}, timeout_multiplier={timeout_multiplier}x)")
    print(f"==================================================\n")

    init_db()
    db = SessionLocal()
    task_keys = list(TASKS.keys())

    # Patch task timeouts for this run
    if timeout_multiplier != 1.0:
        os.environ["LOAD_TEST_TIMEOUT_MULTIPLIER"] = str(timeout_multiplier)

    # Create N runs in DB
    run_ids = []
    for i in range(concurrency_level):
        task_id = task_keys[i % len(task_keys)]
        run = create_task_run(db, task_id)
        run_ids.append(run.id)
    db.close()

    print(f"--> Created {concurrency_level} queued task runs.")
    print(f"--> Launching concurrent worker executions...\n")

    start_time = time.perf_counter()

    # Execute all runs concurrently using asyncio.gather
    results = await asyncio.gather(
        *(execute_task_run_async(rid) for rid in run_ids),
        return_exceptions=True,
    )

    total_duration = time.perf_counter() - start_time

    # Process metrics
    latencies = []
    success_count = 0
    failure_count = 0
    timed_out_count = 0
    exception_count = 0

    for res in results:
        if isinstance(res, Exception):
            exception_count += 1
        elif isinstance(res, dict):
            status = res.get("status")
            if status == "passed":
                success_count += 1
            elif status == "timed_out":
                timed_out_count += 1
            else:
                failure_count += 1
            if res.get("duration_seconds"):
                latencies.append(res["duration_seconds"])

    latencies.sort()
    count = len(latencies)

    p50 = round(latencies[int(count * 0.50)] if count > 0 else 0.0, 2)
    p95 = round(latencies[max(0, math.ceil(count * 0.95) - 1)] if count > 0 else 0.0, 2)
    p99 = round(latencies[max(0, math.ceil(count * 0.99) - 1)] if count > 0 else 0.0, 2)

    tasks_per_min = round((count / total_duration) * 60, 1) if total_duration > 0 else 0.0

    print("---------------- BENCHMARK RESULTS ----------------")
    print(f"Total Concurrent Runs   : {concurrency_level}")
    print(f"Completed (passed)      : {success_count}")
    print(f"Completed (MODEL fail)  : {failure_count}")
    print(f"Timed Out               : {timed_out_count}")
    print(f"Infrastructure Errors   : {exception_count}")
    print(f"Total Elapsed Time      : {round(total_duration, 2)}s")
    print(f"Throughput              : {tasks_per_min} tasks/min")
    print(f"P50 Latency             : {p50}s")
    print(f"P95 Latency             : {p95}s")
    print(f"P99 Latency             : {p99}s")
    print("---------------------------------------------------\n")

    return {
        "concurrency": concurrency_level,
        "throughput_tpm": tasks_per_min,
        "p50_s": p50,
        "p95_s": p95,
        "p99_s": p99,
        "total_time_s": round(total_duration, 2),
        "timed_out": timed_out_count,
    }


if __name__ == "__main__":
    import sys
    level = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    # Use 3x timeout multiplier for concurrent Docker runs to account for
    # shared CPU causing slower LLM round-trips — documented bottleneck.
    asyncio.run(benchmark_concurrent_runs(concurrency_level=level, timeout_multiplier=3.0))

