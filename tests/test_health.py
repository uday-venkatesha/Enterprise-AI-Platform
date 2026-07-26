from fastapi.testclient import TestClient

from app.main import app


# TestClient spins the app up in-process and lets us send fake requests to it.
# No running server needed — this is what makes tests fast and CI-friendly.
client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    # Two things every API test checks: the status code (did it succeed?)...
    assert response.status_code == 200
    # ...and the body (did it return what we expect?).
    body = response.json()
    assert body["status"] == "ok"