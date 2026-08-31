from app.tasks.definitions import list_tasks, get_task, TASKS


def test_list_tasks():
    tasks = list_tasks()
    assert len(tasks) >= 10
    task_ids = [t["id"] for t in tasks]
    assert "billing_escalation" in task_ids
    assert "vip_escalation" in task_ids
    assert "stale_ticket_cleanup" in task_ids


def test_get_task_success():
    task = get_task("billing_escalation")
    assert task.id == "billing_escalation"
    assert task.difficulty == "easy"
    assert callable(task.verifier)


def test_task_difficulties_represented():
    difficulties = {t.difficulty for t in TASKS.values()}
    assert "easy" in difficulties
    assert "medium" in difficulties
    assert "hard" in difficulties
