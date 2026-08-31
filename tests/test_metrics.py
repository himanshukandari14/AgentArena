from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()

    assert "total_runs" in data
    assert "active_runs" in data
    assert "success_rate_percent" in data
    assert "avg_score" in data
    assert "p95_runtime_seconds" in data
    assert "failure_breakdown" in data
    assert "MODEL_FAILURE" in data["failure_breakdown"]


def test_dashboard_route_redirect():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Temporary Redirect to /dashboard
