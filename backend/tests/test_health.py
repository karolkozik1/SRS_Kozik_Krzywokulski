from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_status():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert data["status"] in ["ok", "error"]
     
    assert "backend" in data
    assert isinstance(data["backend"], dict)
    assert data["backend"]["status"] == "running"
    assert data["backend"]["service"] == "FastAPI"
    
    assert "database" in data
    assert isinstance(data["database"], dict)
    assert "connected" in data["database"]
    assert "status" in data["database"]

    assert "statistics" in data
    assert isinstance(data["statistics"], dict)

    assert "checked_at" in data
    assert "response_time_ms" in data
    
def test_health_endpoint_contains_system_statistics():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    statistics = data["statistics"]

    assert "users_count" in statistics
    assert "rooms_count" in statistics
    assert "reservations_count" in statistics
    assert "active_reservations_count" in statistics
    
def test_root_endpoint_returns_message():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "System Rezerwacji działa"}