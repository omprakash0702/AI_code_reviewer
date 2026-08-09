import pytest

import server.jobs as jobs


@pytest.mark.asyncio
async def test_job_starts_in_cloning_state_with_no_inventory_yet():
    # create_job must NOT need file_inventory/total_files upfront — those
    # aren't known until cloning finishes, and create_job is the only thing
    # allowed to happen before the HTTP response goes out.
    analysis_id = await jobs.create_job("https://github.com/x/y", None)
    job = await jobs.get_job(analysis_id)
    assert job["status"] == "cloning"
    assert job["file_inventory"] is None
    assert job["progress"] == {"done": 0, "total": 0, "current_file": None}


@pytest.mark.asyncio
async def test_job_lifecycle():
    analysis_id = await jobs.create_job("https://github.com/x/y", None)

    await jobs.set_scan_complete(analysis_id, {"total_files": 5}, 5, 5, "main")
    job = await jobs.get_job(analysis_id)
    assert job["status"] == "running"
    assert job["file_inventory"] == {"total_files": 5}
    assert job["resolved_ref"] == "main"
    assert job["progress"] == {"done": 0, "total": 5, "current_file": None}

    await jobs.update_progress(analysis_id, 2, 5, "foo.py")
    job = await jobs.get_job(analysis_id)
    assert job["progress"] == {"done": 2, "total": 5, "current_file": "foo.py"}

    await jobs.append_chat_turn(analysis_id, "user", "hello?")
    await jobs.set_result(analysis_id, {"health_score": 90})

    job = await jobs.get_job(analysis_id)
    assert job["status"] == "complete"
    assert job["result"] == {"health_score": 90}
    assert job["chat_history"] == [{"role": "user", "content": "hello?"}]


@pytest.mark.asyncio
async def test_job_failure_during_clone_is_recorded():
    # Cloning can fail before set_scan_complete ever runs — status must go
    # straight from "cloning" to "failed".
    analysis_id = await jobs.create_job("https://github.com/x/y", None)
    await jobs.set_failed(analysis_id, "clone failed")
    job = await jobs.get_job(analysis_id)
    assert job["status"] == "failed"
    assert job["error"] == "clone failed"


@pytest.mark.asyncio
async def test_missing_job_returns_none():
    assert await jobs.get_job("does-not-exist") is None


@pytest.mark.asyncio
async def test_updates_on_missing_job_do_not_raise():
    # These should log a warning and no-op, not crash a background task.
    await jobs.set_scan_complete("missing", {}, 0, 0, "main")
    await jobs.update_progress("missing", 1, 2)
    await jobs.set_result("missing", {})
    await jobs.set_failed("missing", "err")
    await jobs.append_chat_turn("missing", "user", "hi")
