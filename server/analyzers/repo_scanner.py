import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from server.logger import get_logger

log = get_logger("repo_scanner")

IGNORED_DIRS = {
    "node_modules", "venv", "dist", "build", ".git", "__pycache__",
    ".pytest_cache", ".venv", "env", "vendor", "bower_components",
    ".next", ".nuxt", "coverage", "target", "obj", ".idea", ".vscode",
    "migrations", "static", "assets",
}

SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c"}
MAX_FILES = 25
MAX_FILE_SIZE = 60 * 1024  # 60 KB


def clone_repo(repo_url: str, branch: str = None) -> str:
    temp_dir = tempfile.mkdtemp(prefix="pr_guardian_")
    cmd = ["git", "clone", "--depth=1", "--single-branch"]
    if branch:
        cmd.extend(["-b", branch])
    cmd.extend([repo_url, temp_dir])

    log.info("Cloning  %s  →  %s", repo_url, temp_dir)
    if branch:
        log.debug("Branch: %s", branch)

    t0 = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    elapsed = time.perf_counter() - t0

    if result.returncode != 0:
        log.error("Clone FAILED (%.1fs): %s", elapsed, result.stderr.strip())
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Clone failed: {result.stderr.strip()}")

    log.info("Clone complete in %.1fs  →  %s", elapsed, temp_dir)
    return temp_dir


def _should_ignore(parts: tuple) -> bool:
    return any(part in IGNORED_DIRS for part in parts)


def scan_files(repo_dir: str) -> list:
    repo_path = Path(repo_dir)
    files = []
    skipped_size = 0
    skipped_type = 0

    log.info("Scanning files in %s", repo_dir)
    for file_path in repo_path.rglob("*"):
        if not file_path.is_file():
            continue
        rel_parts = file_path.relative_to(repo_path).parts
        if _should_ignore(rel_parts):
            continue
        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            skipped_type += 1
            continue
        try:
            size = file_path.stat().st_size
            if size == 0 or size > MAX_FILE_SIZE:
                skipped_size += 1
                log.debug("Skip (size %d B): %s", size, "/".join(rel_parts))
                continue
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            log.warning("Cannot read %s: %s", "/".join(rel_parts), exc)
            continue

        files.append({
            "filepath": str(file_path),
            "filename": "/".join(rel_parts),
            "content": content,
            "extension": file_path.suffix,
            "size": size,
        })

    log.info(
        "Scan complete: %d eligible files  |  skipped %d unsupported type, %d oversized",
        len(files), skipped_type, skipped_size,
    )
    return files


def _priority_score(f: dict) -> int:
    name = f["filename"].lower()
    score = 0
    if any(x in name for x in ["main.", "app.", "index.", "server.", "api."]):
        score += 100
    if any(x in name for x in ["config", "settings", "setup"]):
        score += 50
    if any(x in name for x in ["auth", "model", "router", "controller", "service"]):
        score += 40
    score -= name.count("/") * 5
    score += min(f["size"] // 1000, 20)
    return score


def scan_repo(repo_url: str, branch: str = None) -> dict:
    temp_dir = None
    t0 = time.perf_counter()
    try:
        temp_dir = clone_repo(repo_url, branch)
        all_files = scan_files(temp_dir)
        total = len(all_files)

        if total > MAX_FILES:
            selected = sorted(all_files, key=_priority_score, reverse=True)[:MAX_FILES]
            log.info(
                "Large repo: selecting top %d/%d files by priority score", MAX_FILES, total
            )
            for f in selected:
                log.debug("  selected: %s  (score=%d)", f["filename"], _priority_score(f))
        else:
            selected = all_files

        log.info(
            "scan_repo done in %.1fs  |  total=%d  analyzing=%d",
            time.perf_counter() - t0, total, len(selected),
        )
        return {
            "success": True,
            "temp_dir": temp_dir,
            "files": selected,
            "total_files_found": total,
            "files_analyzed": len(selected),
        }
    except Exception as exc:
        log.error("scan_repo FAILED after %.1fs: %s", time.perf_counter() - t0, exc)
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "success": False,
            "error": str(exc),
            "files": [],
            "total_files_found": 0,
            "files_analyzed": 0,
        }
