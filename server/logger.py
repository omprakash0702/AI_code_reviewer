"""
Shared logging configuration for PR Guardian AI.
Writes to both the console (INFO+) and logs/pr_guardian.log (DEBUG+).
"""
import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "pr_guardian.log"

_configured = False


def get_logger(name: str) -> logging.Logger:
    global _configured
    if not _configured:
        _configure_root()
        _configured = True
    return logging.getLogger(name)


def _configure_root() -> None:
    LOG_DIR.mkdir(exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d  %(levelname)-7s  [%(name)s]  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # --- console: INFO and above ---
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # --- file: DEBUG and above (full trace) ---
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    root.info("Logging initialised -> %s", LOG_FILE)
