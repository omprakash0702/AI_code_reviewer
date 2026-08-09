from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


def test_review_endpoint(mocker):
    # Without this mock, the endpoint fires a real, billed request to
    # AI_API_URL on every test run — and the old assertions were loose enough
    # to pass even against a missing/broken API key, so the gap went unnoticed.
    mocker.patch(
        "server.ai.model.AISuggester.generate_review",
        return_value={
            "issues": [{"type": "style", "line": 1, "message": "unused var", "confidence": 0.6}],
            "patch": "",
        },
    )

    payload = {
        "filename": "demo.py",
        "code": "print('hello')",
        "analysis": {"lint_issues": []},
    }
    response = client.post("/review", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["issues"] == [
        {"type": "style", "line": 1, "message": "unused var", "confidence": 0.6}
    ]
    assert data["patch"] == ""
    assert data["patched_code"] == "print('hello')"
