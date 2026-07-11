import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the AAYUDH News Assistant API"}
