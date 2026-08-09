import time
from unittest import mock

from fastapi.testclient import TestClient

FAKE_SCAN = {
    "success": True,
    "temp_dir": None,  # filled in per-test with a real temp dir so cleanup doesn't error
    "files": [
        {"filepath": "a.py", "filename": "a.py", "content": "x = 1", "extension": ".py", "size": 5},
        {"filepath": "b.py", "filename": "b.py", "content": "y = 2", "extension": ".py", "size": 5},
    ],
    "total_files_found": 2,
    "files_analyzed": 2,
    "file_inventory": {
        "total_files": 5, "by_extension": {".py": 2, ".md": 3},
        "supported": 2, "skipped_unsupported_type": 3, "skipped_oversized": 0, "skipped_unreadable": 0,
    },
    "resolved_ref": "main",
}


def _patched(tmp_path):
    scan = dict(FAKE_SCAN, temp_dir=str(tmp_path))
    return [
        mock.patch("server.app.scan_repo", return_value=scan),
        mock.patch("server.app.analyze_file", return_value={"language": "python", "lint_issues": [], "security_issues": [], "errors": []}),
        mock.patch("server.ai.repo_reviewer.RepoReviewer.review_file_enhanced_async", new=mock.AsyncMock(return_value={"issues": [], "patch": ""})),
        mock.patch("server.ai.repo_reviewer.RepoReviewer.generate_repo_intelligence", return_value={
            "repo_type": "test", "architecture_summary": "demo", "important_modules": [],
            "detected_frameworks": [], "primary_language": "Python",
        }),
        mock.patch("server.ai.repo_reviewer.RepoReviewer.generate_pr_summary", return_value={
            "main_findings": "ok", "recommendation": "approve", "recommendation_reason": "clean",
        }),
        mock.patch("server.ai.repo_reviewer.RepoReviewer.generate_critical_analysis", return_value={
            "systemic_patterns": [], "top_risk": None, "priority_recommendations": [],
        }),
    ]


def test_analyze_repo_start_returns_instantly_before_cloning(tmp_path):
    # Regression test: /analyze-repo used to clone the repo synchronously
    # before responding, so a slow/large clone could trip the frontend's
    # request timeout even though the backend was working fine. The clone
    # must happen only in the background task, never on this response path.
    patches = _patched(tmp_path)
    for p in patches:
        p.start()
    try:
        from server.app import app
        client = TestClient(app)

        start = client.post("/analyze-repo", json={"repo_url": "https://github.com/x/y"})
        assert start.status_code == 200
        body = start.json()
        assert set(body.keys()) == {"analysis_id"}  # nothing else — no clone-dependent data yet
    finally:
        for p in patches:
            p.stop()


def test_analyze_repo_full_job_flow(tmp_path):
    patches = _patched(tmp_path)
    for p in patches:
        p.start()
    try:
        from server.app import app
        client = TestClient(app)

        start = client.post("/analyze-repo", json={"repo_url": "https://github.com/x/y"})
        assert start.status_code == 200
        analysis_id = start.json()["analysis_id"]

        status = None
        for _ in range(20):
            status = client.get(f"/analysis/{analysis_id}/status").json()
            if status["status"] in ("complete", "failed"):
                break
            time.sleep(0.1)
        assert status["status"] == "complete"
        assert status["file_inventory"]["total_files"] == 5
        assert status["total_files_found"] == 2
        assert status["progress"] == {"done": 2, "total": 2, "current_file": "b.py"}

        result = client.get(f"/analysis/{analysis_id}")
        assert result.status_code == 200
        result_body = result.json()
        assert result_body["health_score"] == 100
        assert len(result_body["file_results"]) == 2

        with mock.patch("server.ai.chat.answer_question", new=mock.AsyncMock(return_value="It's a simple demo repo.")):
            chat_resp = client.post(f"/analysis/{analysis_id}/chat", json={"message": "what does this repo do?"})
        assert chat_resp.status_code == 200
        assert chat_resp.json() == {"answer": "It's a simple demo repo."}
    finally:
        for p in patches:
            p.stop()


def test_clone_failure_is_reported_via_status_not_the_start_response():
    # Since cloning now happens after the response goes out, a bad repo URL
    # can no longer be a 400 on POST /analyze-repo — it surfaces as
    # status: "failed" once the background task actually tries to clone.
    bad_scan = {"success": False, "error": "Clone failed: repository not found", "files": [],
                "total_files_found": 0, "files_analyzed": 0, "file_inventory": {}, "resolved_ref": None}
    with mock.patch("server.app.scan_repo", return_value=bad_scan):
        from server.app import app
        client = TestClient(app)

        start = client.post("/analyze-repo", json={"repo_url": "not-a-real-url"})
        assert start.status_code == 200
        analysis_id = start.json()["analysis_id"]

        status = None
        for _ in range(20):
            status = client.get(f"/analysis/{analysis_id}/status").json()
            if status["status"] == "failed":
                break
            time.sleep(0.1)
        assert status["status"] == "failed"
        assert "not found" in status["error"]


def test_status_and_result_404_for_unknown_analysis():
    from server.app import app
    client = TestClient(app)
    assert client.get("/analysis/does-not-exist/status").status_code == 404
    assert client.get("/analysis/does-not-exist").status_code == 404


def test_result_409_while_still_running():
    # A job record that's still cloning/running (never completed) — exercises
    # the "not ready yet" branch without racing a real background task.
    import asyncio

    from server.app import app
    import server.jobs as jobs

    analysis_id = asyncio.get_event_loop().run_until_complete(
        jobs.create_job("https://github.com/x/y", None)
    )
    client = TestClient(app)
    resp = client.get(f"/analysis/{analysis_id}")
    assert resp.status_code == 409

    chat_resp = client.post(f"/analysis/{analysis_id}/chat", json={"message": "hi"})
    assert chat_resp.status_code == 409


def test_one_hung_file_does_not_stall_the_whole_job(tmp_path, monkeypatch):
    # Regression test: server/analyzers/common.py's run_command used to have
    # no subprocess timeout, and asyncio.gather waits for every task — so one
    # file whose static analysis hung would silently stall the ENTIRE job
    # forever, no matter how many other files were done. FILE_TIMEOUT_SECONDS
    # + the per-tool subprocess timeout together guarantee every file resolves.
    import asyncio

    import server.app as app_module
    import server.jobs as jobs

    monkeypatch.setattr(app_module, "FILE_TIMEOUT_SECONDS", 1)

    files = [
        {"filepath": "hang.py", "filename": "hang.py", "content": "x=1", "extension": ".py", "size": 3},
        {"filepath": "fine.py", "filename": "fine.py", "content": "y=2", "extension": ".py", "size": 3},
    ]
    scan = {
        "success": True, "temp_dir": str(tmp_path), "files": files,
        "total_files_found": 2, "files_analyzed": 2, "file_inventory": {}, "resolved_ref": "main",
    }

    async def fake_to_thread(func, *args):
        # asyncio.to_thread is used for scan_repo(), analyze_file(), AND the
        # repo intelligence / PR summary / critical analysis calls — only
        # analyze_file() on "hang.py" should actually hang here.
        if func is app_module.scan_repo:
            return scan
        if func is app_module.analyze_file:
            filepath = args[0]
            if "hang" in filepath:
                await asyncio.sleep(999)  # would hang forever pre-fix
            return {"lint_issues": [], "security_issues": [], "errors": []}
        return func(*args)

    async def fake_review_async(filename, content, analysis, client):
        return {"issues": [], "patch": ""}

    with mock.patch.object(app_module.asyncio, "to_thread", fake_to_thread), \
         mock.patch.object(app_module.repo_reviewer, "review_file_enhanced_async", fake_review_async), \
         mock.patch.object(app_module.repo_reviewer, "generate_repo_intelligence", return_value={"repo_type": "t"}), \
         mock.patch.object(app_module.repo_reviewer, "generate_pr_summary", return_value={}), \
         mock.patch.object(app_module.repo_reviewer, "generate_critical_analysis", return_value={}):

        analysis_id = asyncio.get_event_loop().run_until_complete(
            jobs.create_job("https://github.com/x/y", None)
        )

        # If the bug were still present this would hang forever — the
        # wait_for here is just so a real regression fails the test instead
        # of hanging the whole suite.
        asyncio.get_event_loop().run_until_complete(
            asyncio.wait_for(
                app_module._run_analysis_job(analysis_id, "https://github.com/x/y", None),
                timeout=10,
            )
        )

        job = asyncio.get_event_loop().run_until_complete(jobs.get_job(analysis_id))
        assert job["status"] == "complete"
        filenames = {f["filename"] for f in job["result"]["file_results"]}
        assert filenames == {"hang.py", "fine.py"}
