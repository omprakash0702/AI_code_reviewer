from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

def test_review_endpoint():
    payload = {
        "filename": "demo.py",
        "code": "print('hello')",
        "analysis": {"lint_issues": []}
    }
    response = client.post("/review", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "issues" in data
    assert "patch" in data
