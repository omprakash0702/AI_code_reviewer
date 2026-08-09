import json
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

# We used to only AI-review an 8-extension allowlist. Now: review ANY
# text-based file, and only exclude what genuinely can't/shouldn't be
# reviewed as code — binaries, media, archives, and generated/lock files
# that are huge and near-zero-signal.
BLOCKED_EXTENSIONS = {
    # images / media / fonts
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".tiff", ".avif",
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv", ".flac", ".ogg", ".webm",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    # archives / packages / compiled artifacts
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".rar", ".7z",
    ".whl", ".jar", ".war", ".ear", ".exe", ".dll", ".so", ".dylib",
    ".bin", ".class", ".pyc", ".pyd", ".o", ".a", ".obj",
    # documents / data blobs
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".db", ".sqlite", ".sqlite3",
    ".lock",
}

# Exact filenames that are always generated/huge and not worth AI review,
# regardless of extension.
BLOCKED_FILENAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
    "Cargo.lock", "composer.lock", "Gemfile.lock", "go.sum",
}

# Suffixes (not full extensions) that indicate generated/minified/bundled output.
BLOCKED_NAME_SUFFIXES = (".min.js", ".min.css", ".map", ".d.ts")

MAX_FILES = 300
MAX_FILE_SIZE = 60 * 1024          # 60 KB for most files
MAX_NOTEBOOK_SIZE = 400 * 1024     # notebooks carry embedded output/images we strip out


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


def get_resolved_ref(repo_dir: str) -> str:
    """The actual branch name git checked out — needed later so the chatbot
    fetches file content from the same ref that was analyzed, even when the
    caller didn't specify one and git picked the repo's default branch."""
    result = subprocess.run(
        ["git", "-C", repo_dir, "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, timeout=10,
    )
    ref = result.stdout.strip()
    return ref if result.returncode == 0 and ref else "HEAD"


def _should_ignore(parts: tuple) -> bool:
    return any(part in IGNORED_DIRS for part in parts)


def _is_blocked(file_path: Path) -> bool:
    if file_path.name in BLOCKED_FILENAMES:
        return True
    name_lower = file_path.name.lower()
    if any(name_lower.endswith(suf) for suf in BLOCKED_NAME_SUFFIXES):
        return True
    return file_path.suffix.lower() in BLOCKED_EXTENSIONS


def _looks_binary(sample: bytes) -> bool:
    # Text files essentially never contain a NUL byte; binary formats we
    # don't already recognize by extension almost always do somewhere in
    # their first few KB.
    return b"\x00" in sample


def _extract_notebook_code(raw_text: str) -> str:
    """Jupyter notebooks are JSON with huge amounts of metadata/output noise
    (including base64-embedded images) mixed in with the actual code. Pull
    out just the code cells so AI review spends its budget on code, not JSON
    scaffolding."""
    try:
        nb = json.loads(raw_text)
    except (json.JSONDecodeError, ValueError):
        return raw_text

    parts = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        if source.strip():
            parts.append(source)

    return "\n\n# --- next cell ---\n\n".join(parts)


def scan_files(repo_dir: str) -> tuple:
    """Walks every file in the repo once, returning (eligible_files, inventory).

    eligible_files: files that are AI-reviewable — any text-based file that
    isn't a binary/archive/generated-lock file, readable, and sized OK.
    inventory: a full breakdown of EVERY file found, by extension — including
    types we don't AI-review — so the dashboard can show what's actually in
    the repo, not just the reviewable subset.
    """
    repo_path = Path(repo_dir)
    files = []
    ext_counts: dict = {}
    total_all_files = 0
    skipped_unsupported_type = 0
    skipped_oversized = 0
    skipped_unreadable = 0

    log.info("Scanning files in %s", repo_dir)
    for file_path in repo_path.rglob("*"):
        if not file_path.is_file():
            continue
        rel_parts = file_path.relative_to(repo_path).parts
        if _should_ignore(rel_parts):
            continue

        total_all_files += 1
        ext = file_path.suffix.lower() or "(no extension)"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1

        if _is_blocked(file_path):
            skipped_unsupported_type += 1
            continue

        is_notebook = file_path.suffix.lower() == ".ipynb"
        size_limit = MAX_NOTEBOOK_SIZE if is_notebook else MAX_FILE_SIZE

        try:
            size = file_path.stat().st_size
            if size == 0 or size > size_limit:
                skipped_oversized += 1
                log.debug("Skip (size %d B): %s", size, "/".join(rel_parts))
                continue

            with open(file_path, "rb") as fh:
                sample = fh.read(2048)
            if _looks_binary(sample):
                skipped_unsupported_type += 1
                continue

            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if is_notebook:
                content = _extract_notebook_code(content)
                if not content.strip():
                    skipped_unsupported_type += 1
                    continue
        except OSError as exc:
            skipped_unreadable += 1
            log.warning("Cannot read %s: %s", "/".join(rel_parts), exc)
            continue

        files.append({
            "filepath": str(file_path),
            "filename": "/".join(rel_parts),
            "content": content,
            "extension": file_path.suffix,
            "size": size,
        })

    inventory = {
        "total_files": total_all_files,
        "by_extension": dict(sorted(ext_counts.items(), key=lambda kv: -kv[1])),
        "supported": len(files),
        "skipped_unsupported_type": skipped_unsupported_type,
        "skipped_oversized": skipped_oversized,
        "skipped_unreadable": skipped_unreadable,
    }

    log.info(
        "Scan complete: %d/%d eligible  |  skipped %d unsupported type, %d oversized, %d unreadable",
        len(files), total_all_files, skipped_unsupported_type, skipped_oversized, skipped_unreadable,
    )
    return files, inventory


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
        resolved_ref = get_resolved_ref(temp_dir)
        all_files, inventory = scan_files(temp_dir)
        total = len(all_files)

        if total > MAX_FILES:
            selected = sorted(all_files, key=_priority_score, reverse=True)[:MAX_FILES]
            log.info(
                "Large repo: selecting top %d/%d eligible files by priority score", MAX_FILES, total
            )
        else:
            selected = all_files

        log.info(
            "scan_repo done in %.1fs  |  eligible=%d  analyzing=%d  ref=%s",
            time.perf_counter() - t0, total, len(selected), resolved_ref,
        )
        return {
            "success": True,
            "temp_dir": temp_dir,
            "files": selected,
            "total_files_found": total,
            "files_analyzed": len(selected),
            "file_inventory": inventory,
            "resolved_ref": resolved_ref,
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
            "file_inventory": {},
            "resolved_ref": None,
        }
