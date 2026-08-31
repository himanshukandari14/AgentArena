from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_tasks_endpoint():
    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert len(data["tasks"]) >= 10


@patch("app.api.runs.execute_task_run_async", new_callable=AsyncMock)
def test_trigger_run_and_retrieve(mock_worker):
    response = client.post("/runs", json={"task_id": "billing_escalation"})
    assert response.status_code == 202
    run_data = response.json()
    assert "run_id" in run_data
    run_id = run_data["run_id"]

    get_res = client.get(f"/runs/{run_id}")
    assert get_res.status_code == 200
    details = get_res.json()
    assert details["id"] == run_id
    assert details["task_id"] == "billing_escalation"


def test_list_runs_endpoint():
    response = client.get("/runs")
    assert response.status_code == 200
    runs = response.json()
    assert isinstance(runs, list)
