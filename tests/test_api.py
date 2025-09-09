import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/v1/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_readiness_check():
    """Test readiness check endpoint"""
    response = client.get("/api/v1/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

def test_docs_available():
    """Test that API documentation is available"""
    response = client.get("/api/v1/docs")
    assert response.status_code == 200

def test_openapi_spec():
    """Test OpenAPI specification is available"""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["info"]["title"] == "Student Chat + Ingestion API"
