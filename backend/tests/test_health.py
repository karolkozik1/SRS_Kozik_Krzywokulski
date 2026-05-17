from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_status():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "backend" in data
    assert data["backend"] == "running"
    
    
def test_root_endpoint_returns_message():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "System Rezerwacji działa"}