"""Redis-backed store for async /analyze-repo jobs.

Each analysis is a single JSON blob under key `analysis:{id}`, written by one
background task at a time — simple, no need for Redis hashes/transactions
for this access pattern. Falls back to an in-process fakeredis instance when
REDIS_URL isn't set, so local dev/tests don't need a real Redis server; state
just won't survive a restart in that mode.
"""
import json
import os
import time
import uuid
from typing import Optional

from dotenv import load_dotenv

from server.logger import get_logger

load_dotenv()
log = get_logger("jobs")

JOB_TTL_SECONDS = 24 * 60 * 60  # 24h — old analyses expire instead of piling up


def _make_client():
    url = os.getenv("REDIS_URL")
    if url:
        import redis.asyncio as redis
        log.info("jobs: using Redis at %s", url)
        return redis.from_url(url, decode_responses=True)

    import fakeredis.aioredis
    log.warning("jobs: REDIS_URL not set — using in-process fakeredis (state lost on restart)")
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


_client = _make_client()


def _key(analysis_id: str) -> str:
    return f"analysis:{analysis_id}"


async def _save(analysis_id: str, record: dict) -> None:
    await _client.set(_key(analysis_id), json.dumps(record), ex=JOB_TTL_SECONDS)


async def create_job(repo_url: str, branch: Optional[str]) -> str:
    """Creates a job in the "cloning" state — file_inventory and progress.total
    aren't known yet because the clone itself hasn't run. This is deliberately
    the ONLY thing that happens before the HTTP response goes out: cloning a
    repo is network-bound and can take anywhere from 1s to 30s+ depending on
    GitHub/network conditions, so it must never be on the critical path of a
    request the frontend is waiting on with a fixed timeout."""
    analysis_id = uuid.uuid4().hex
    record = {
        "analysis_id": analysis_id,
        "status": "cloning",
        "error": None,
        "repo_url": repo_url,
        "branch": branch,
        "resolved_ref": None,
        "file_inventory": None,
        "total_files_found": None,
        "progress": {"done": 0, "total": 0, "current_file": None},
        "result": None,
        "chat_history": [],
        "created_at": time.time(),
    }
    await _save(analysis_id, record)
    log.info("jobs: created %s (cloning)", analysis_id)
    return analysis_id


async def get_job(analysis_id: str) -> Optional[dict]:
    raw = await _client.get(_key(analysis_id))
    if raw is None:
        return None
    return json.loads(raw)


async def set_scan_complete(
    analysis_id: str, file_inventory: dict, total_files_found: int, files_to_analyze: int, resolved_ref: str
) -> None:
    """Called once cloning + scanning finishes — this is when we first learn
    how many files there are, so progress.total is set here, not at creation."""
    record = await get_job(analysis_id)
    if record is None:
        log.warning("jobs: set_scan_complete on missing job %s", analysis_id)
        return
    record["status"] = "running"
    record["file_inventory"] = file_inventory
    record["total_files_found"] = total_files_found
    record["resolved_ref"] = resolved_ref
    record["progress"] = {"done": 0, "total": files_to_analyze, "current_file": None}
    await _save(analysis_id, record)


async def update_progress(analysis_id: str, done: int, total: int, current_file: Optional[str] = None) -> None:
    record = await get_job(analysis_id)
    if record is None:
        log.warning("jobs: update_progress on missing job %s", analysis_id)
        return
    record["progress"] = {"done": done, "total": total, "current_file": current_file}
    await _save(analysis_id, record)


async def set_result(analysis_id: str, result: dict) -> None:
    record = await get_job(analysis_id)
    if record is None:
        log.warning("jobs: set_result on missing job %s", analysis_id)
        return
    record["result"] = result
    record["status"] = "complete"
    await _save(analysis_id, record)


async def set_failed(analysis_id: str, error: str) -> None:
    record = await get_job(analysis_id)
    if record is None:
        log.warning("jobs: set_failed on missing job %s", analysis_id)
        return
    record["status"] = "failed"
    record["error"] = error
    await _save(analysis_id, record)


async def append_chat_turn(analysis_id: str, role: str, content: str) -> None:
    record = await get_job(analysis_id)
    if record is None:
        log.warning("jobs: append_chat_turn on missing job %s", analysis_id)
        return
    record.setdefault("chat_history", []).append({"role": role, "content": content})
    await _save(analysis_id, record)
