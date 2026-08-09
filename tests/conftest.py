import os

# Tests must be hermetic — they must not silently change behavior based on
# whatever happens to be in the developer's local .env (e.g. a real
# REDIS_URL pointing at Docker Redis). Force the in-process fakeredis
# fallback so test behavior is deterministic on every machine.
#
# This also sidesteps a real asyncio issue: a real redis.asyncio client is a
# module-level singleton in server/jobs.py, created once at import time and
# bound to whichever event loop existed then. pytest-asyncio gives each test
# function its own event loop, so a shared real-Redis connection object
# reused across tests fails with "attached to a different loop." fakeredis
# doesn't hit this because it isn't a real network connection.
os.environ["REDIS_URL"] = ""
