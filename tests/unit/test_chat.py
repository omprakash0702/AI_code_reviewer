from unittest import mock

import pytest

import server.ai.chat as chat
from server.ai.repo_reviewer import RepoReviewer


def _job(**overrides):
    job = {
        "repo_url": "https://github.com/octocat/Hello-World",
        "branch": None,
        "resolved_ref": "master",
        "file_inventory": {"total_files": 2, "by_extension": {".py": 1, ".md": 1}},
        "chat_history": [],
        "result": {
            "health_score": 90,
            "files_analyzed": 1,
            "repository_intelligence": {"repo_type": "Demo", "architecture_summary": "Simple demo."},
            "issues": {"security": [], "performance": [], "bugs": [], "code_quality": []},
            "critical_analysis": {"top_risk": None},
            "file_results": [{"filename": "app.py", "issues": [], "patch": ""}],
        },
    }
    job.update(overrides)
    return job


def test_parse_owner_repo():
    assert chat._parse_owner_repo("https://github.com/octocat/Hello-World") == ("octocat", "Hello-World")
    assert chat._parse_owner_repo("https://github.com/octocat/Hello-World.git") == ("octocat", "Hello-World")
    assert chat._parse_owner_repo("not a url") == (None, None)


def test_known_file_paths_from_file_results():
    job = _job()
    assert chat._known_file_paths(job) == ["app.py"]


@pytest.mark.asyncio
async def test_answer_question_skips_file_fetch_when_not_needed():
    job = _job()
    calls = []

    async def fake_call_async(self, label, prompt, client):
        calls.append(label)
        if label == "chat_pick_files":
            return {"files_needed": []}
        return {"answer": "Health score is 90/100."}

    with mock.patch.object(RepoReviewer, "_call_async", fake_call_async):
        answer = await chat.answer_question(job, "what's the health score?")

    assert calls == ["chat_pick_files", "chat_answer"]
    assert answer == "Health score is 90/100."


@pytest.mark.asyncio
async def test_answer_question_ignores_hallucinated_file_paths():
    # The model must only be able to pick from files we know exist —
    # otherwise it could "ask" for a path that was never in the repo.
    job = _job()

    async def fake_call_async(self, label, prompt, client):
        if label == "chat_pick_files":
            return {"files_needed": ["totally/made/up/path.py"]}
        return {"answer": "done"}

    fetch_calls = []

    async def fake_fetch(client, owner, repo, ref, path):
        fetch_calls.append(path)
        return "should not be called"

    with mock.patch.object(RepoReviewer, "_call_async", fake_call_async), \
         mock.patch.object(chat, "_fetch_raw_file", fake_fetch):
        await chat.answer_question(job, "explain the made up file")

    assert fetch_calls == []


@pytest.mark.asyncio
async def test_answer_question_handles_ai_failure_gracefully():
    job = _job()

    async def failing_call(self, label, prompt, client):
        raise RuntimeError("AI is down")

    with mock.patch.object(RepoReviewer, "_call_async", failing_call):
        answer = await chat.answer_question(job, "anything")

    assert "error" in answer.lower()
