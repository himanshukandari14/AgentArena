from app.services.evaluator import calculate_score, classify_failure
from app.tasks.definitions import get_task


def test_calculate_score_passed():
    verifier_res = {"passed": True, "score": 1.0}
    score = calculate_score(verifier_res, executed_steps=5, max_steps=20)
    assert score >= 0.80
    assert score <= 1.00


def test_calculate_score_failed():
    verifier_res = {"passed": False, "score": 0.5}
    score = calculate_score(verifier_res, executed_steps=10, max_steps=20)
    assert score == 0.20


def test_classify_failure_model_failure():
    task_def = get_task("billing_escalation")
    verifier_res = {"passed": False, "reason": "Tickets not assigned to Billing"}
    cat, reason = classify_failure(task_def, verifier_res, tool_error_count=0)
    assert cat == "MODEL_FAILURE"
    assert "Billing" in reason


def test_classify_failure_environment_failure():
    task_def = get_task("billing_escalation")
    verifier_res = {"passed": False, "reason": "Failed"}
    cat, reason = classify_failure(
        task_def, verifier_res, agent_error="DB ConnectionRefusedError"
    )
    assert cat == "ENVIRONMENT_FAILURE"


def test_classify_failure_success():
    task_def = get_task("billing_escalation")
    verifier_res = {"passed": True, "reason": "All set"}
    cat, reason = classify_failure(task_def, verifier_res)
    assert cat == "NONE"
