"""Chatbot for asking follow-up questions about a completed /analyze-repo job.

Two-call retrieval pattern per question, no repo clone kept around:
  1. Ask the model which specific files (if any) it needs to read to answer.
  2. Fetch just those files' raw content from GitHub on demand, then answer.
This lets it read any file in the repo — not just ones already flagged as an
issue — without storing the whole clone anywhere after the initial scan.
"""
import re

import httpx
from dotenv import load_dotenv

from server.ai.repo_reviewer import RepoReviewer
from server.logger import get_logger

load_dotenv()
log = get_logger("chat")

MAX_FILES_PER_ANSWER = 3
MAX_FILE_CHARS = 6000
MAX_KNOWN_FILES_LISTED = 150
GITHUB_URL_RE = re.compile(r"github\.com/([^/]+)/([^/]+?)(\.git)?/?$")


def _parse_owner_repo(repo_url: str):
    m = GITHUB_URL_RE.search((repo_url or "").strip())
    if not m:
        return None, None
    return m.group(1), m.group(2)


async def _fetch_raw_file(client: httpx.AsyncClient, owner: str, repo: str, ref: str, path: str) -> str:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
    try:
        resp = await client.get(url, timeout=15)
        if resp.status_code != 200:
            log.warning("chat: could not fetch %s (HTTP %d)", path, resp.status_code)
            return ""
        return resp.text[:MAX_FILE_CHARS]
    except Exception as exc:
        log.warning("chat: fetch failed for %s: %s", path, exc)
        return ""


def _build_context_digest(job: dict) -> str:
    inventory = job.get("file_inventory") or {}
    result = job.get("result") or {}
    issues = result.get("issues", {})

    lines = [
        f"Repo: {job.get('repo_url')}",
        f"Health score: {result.get('health_score', '?')}/100",
        f"Total files in repo: {inventory.get('total_files', '?')}  "
        f"(AI-reviewed: {result.get('files_analyzed', '?')})",
    ]
    by_ext = inventory.get("by_extension") or {}
    if by_ext:
        ext_summary = ", ".join(f"{ext}: {count}" for ext, count in list(by_ext.items())[:15])
        lines.append(f"File types: {ext_summary}")

    intel = result.get("repository_intelligence") or {}
    if intel.get("architecture_summary"):
        lines.append(f"Architecture: {intel['architecture_summary']}")
    if intel.get("repo_type"):
        lines.append(f"Repo type: {intel['repo_type']}")

    for category, cat_issues in issues.items():
        if not cat_issues:
            continue
        lines.append(f"\n{category.upper()} issues ({len(cat_issues)}):")
        for issue in cat_issues[:20]:
            lines.append(
                f"  - [{issue.get('severity', '?')}] {issue.get('filename', '?')}: {issue.get('title', '')}"
            )

    critical = result.get("critical_analysis") or {}
    top_risk = critical.get("top_risk")
    if top_risk:
        lines.append(f"\nTop risk: {top_risk.get('title')} — {top_risk.get('description')}")

    return "\n".join(lines)


def _known_file_paths(job: dict) -> list:
    result = job.get("result") or {}
    return [f["filename"] for f in result.get("file_results", []) if f.get("filename")]


async def answer_question(job: dict, message: str, reviewer: RepoReviewer = None) -> str:
    reviewer = reviewer or RepoReviewer()
    digest = _build_context_digest(job)
    history = job.get("chat_history") or []
    history_text = "\n".join(f"{t['role']}: {t['content']}" for t in history[-6:])

    owner, repo = _parse_owner_repo(job.get("repo_url", ""))
    ref = job.get("resolved_ref") or job.get("branch") or "HEAD"
    known_files = _known_file_paths(job)[:MAX_KNOWN_FILES_LISTED]
    known_files_text = "\n".join(f"- {f}" for f in known_files) or "(none listed)"

    async with httpx.AsyncClient() as client:
        # Step 1: does this question need to actually read specific source files?
        pick_prompt = f"""You are deciding what's needed to answer a developer's question about
a GitHub repository. Return ONLY valid JSON with no extra text.

Analysis summary:
{digest}

Files that exist in this repo (pick only from this list — paths outside it will fail to fetch):
{known_files_text}

Conversation so far:
{history_text}

Question: {message}

If the analysis summary above is already enough to answer, return an empty list.
Otherwise list up to {MAX_FILES_PER_ANSWER} file paths (from the list above) you
need to read to answer accurately.

Return exactly: {{"files_needed": ["path/to/file.py"]}}"""
        try:
            pick = await reviewer._call_async("chat_pick_files", pick_prompt, client)
            files_needed = [f for f in pick.get("files_needed", []) if f in known_files][:MAX_FILES_PER_ANSWER]
        except Exception as exc:
            log.warning("chat: file-pick step failed, answering from summary only: %s", exc)
            files_needed = []

        file_contents = ""
        if files_needed and owner and repo:
            for path in files_needed:
                content = await _fetch_raw_file(client, owner, repo, ref, path)
                if content:
                    file_contents += f"\n\n### {path}\n```\n{content}\n```"

        source_block = f"\nSource code you requested:{file_contents}" if file_contents else ""
        answer_prompt = f"""You are a helpful assistant answering questions about a GitHub repository
that PR Guardian AI just analyzed. Answer directly and specifically — reference
actual file names, issues, or code when relevant. Don't pad with generic advice.
Return ONLY valid JSON with no extra text.

Analysis summary:
{digest}
{source_block}

Conversation so far:
{history_text}

Question: {message}

Return exactly: {{"answer": "your answer as plain text, no markdown code fences"}}"""
        try:
            result = await reviewer._call_async("chat_answer", answer_prompt, client)
            answer = (result.get("answer") or "").strip()
            return answer or "I couldn't come up with an answer — try rephrasing the question."
        except Exception as exc:
            log.error("chat: answer step failed: %s", exc)
            return "Sorry, I hit an error trying to answer that. Please try again."
