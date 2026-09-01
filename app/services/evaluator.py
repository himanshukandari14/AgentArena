from sqlalchemy.orm import Session

from app.tasks.definitions import TaskDefinition


def classify_failure(
    task_def: TaskDefinition,
    verifier_result: dict,
    agent_error: str | None = None,
    tool_error_count: int = 0,
    executed_steps: int = 0,
) -> tuple[str, str]:
    """
    Signature Feature: Failure Attribution Classifier
    Classifies run outcomes into:
      - NONE: Success
      - ENVIRONMENT_FAILURE: Infrastructure, DB, or tool runner crash/exception
      - TASK_FAILURE: Invalid task definition or broken verifier contract
      - MODEL_FAILURE: Agent decision failure, invalid arguments, or missing steps
    """
    if verifier_result.get("passed", False):
        return "NONE", "Task completed successfully."

    # 1. Environment Failure Detection
    if agent_error:
        env_error_keywords = ["ConnectionRefused", "DB", "Crash", "402", "401", "429", "APIError", "credits", "APIKey", "Quota"]
        if any(kw in agent_error for kw in env_error_keywords):
            return "ENVIRONMENT_FAILURE", f"Infrastructure or API error: {agent_error}"

    if "verifier_exception" in verifier_result:
        return "ENVIRONMENT_FAILURE", f"Environment error during verification: {verifier_result['verifier_exception']}"

    # 2. Task Failure Detection
    if verifier_result.get("reason", "").startswith("Task configuration error"):
        return "TASK_FAILURE", f"Task contract error: {verifier_result.get('reason')}"

    # 3. Model Failure Detection
    reason = verifier_result.get("reason", "Agent failed to achieve expected state.")
    if tool_error_count > 3:
        reason += f" Agent made {tool_error_count} malformed tool calls."
    if executed_steps >= 20:
        reason += " Agent reached maximum iteration limit without completing task."

    return "MODEL_FAILURE", reason


def calculate_score(
    verifier_result: dict,
    executed_steps: int,
    max_steps: int = 20,
) -> float:
    """
    Calculates deterministic 0.0 - 1.0 score based on:
      - Functional correctness (60%)
      - State correctness (20%)
      - Efficiency / Step economy (20%)
    """
    if not verifier_result.get("passed", False):
        partial_state_score = float(verifier_result.get("score", 0.0))
        # Partial state correctness up to 40% total
        return round(partial_state_score * 0.4, 2)

    # Base score for passing functional & state verification (80%)
    base_score = 0.80

    # Efficiency bonus (up to 20%)
    efficiency_bonus = max(0.0, (max_steps - executed_steps) / max_steps) * 0.20

    return round(base_score + efficiency_bonus, 2)


def evaluate_task_run(
    db: Session,
    task_def: TaskDefinition,
    executed_steps: int,
    tool_error_count: int = 0,
    agent_error: str | None = None,
) -> dict:
    """
    Runs verification, calculates score, and attributes failure category.
    """
    try:
        verifier_result = task_def.verifier(db)
    except Exception as e:
        verifier_result = {
            "passed": False,
            "score": 0.0,
            "reason": f"Verifier exception: {str(e)}",
            "verifier_exception": str(e),
        }

    failure_cat, failure_reason = classify_failure(
        task_def=task_def,
        verifier_result=verifier_result,
        agent_error=agent_error,
        tool_error_count=tool_error_count,
        executed_steps=executed_steps,
    )

    final_score = calculate_score(
        verifier_result=verifier_result,
        executed_steps=executed_steps,
    )

    return {
        "passed": verifier_result.get("passed", False),
        "score": final_score,
        "failure_category": failure_cat,
        "failure_reason": failure_reason,
        "verifier_details": verifier_result,
    }
