import asyncio
import json
import re
import shutil
import time

from dotenv import load_dotenv

load_dotenv()

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import server.jobs as jobs
from server.ai import chat
from server.ai.model import AISuggester
from server.ai.repo_reviewer import RepoReviewer
from server.ai.validation import validate_ai_output
from server.analyzers import analyze_file
from server.analyzers.repo_scanner import scan_repo
from server.diff.classify import classify_patch
from server.diff.safe_apply import safe_apply_patch
from server.diff.validate_patch import is_meaningful_patch
from server.logger import get_logger
from server.schemas.repo_analysis import RepoAnalysisRequest
from server.schemas.review_request import ReviewRequest
from server.schemas.review_response import ReviewResponse

log = get_logger("app")

app = FastAPI(title="PR Guardian AI")

# /analyze-repo kicks off a background job that can run 100s of AI API calls
# (repo intelligence + up to 300 files + critical analysis + PR summary) —
# with no auth on a public deploy, an unbounded endpoint here means anyone
# can run up the operator's AI bill arbitrarily. Rate-limit job starts by IP
# as a baseline guard.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai = AISuggester()
repo_reviewer = RepoReviewer()
log.info("PR Guardian AI started")

# How many files get AI-reviewed concurrently within one analysis job. Bounds
# both wall-clock time and how hard we hammer the AI provider at once. 10 is
# tuned so a ~150-file "medium" repo lands comfortably under 3 minutes with
# real margin for variance, not right at the edge. If this trips the AI
# provider's own rate limits in practice, that's the knob to turn back down —
# review_file_enhanced_async already degrades a failed call to "no issues
# found" for that file rather than crashing the job, so a 429 costs one
# file's findings, not the whole run.
FILE_REVIEW_CONCURRENCY = 10

# Hard ceiling per file: 4 static-analysis tools at up to 30s each (see
# common.COMMAND_TIMEOUT) plus a 60s AI call, worst case. Without this, one
# stuck file — even after the per-tool timeout fix — could still stall the
# whole job's progress; this guarantees every file resolves one way or another.
FILE_TIMEOUT_SECONDS = 180

# Rough per-file AI review time used only to show the user an ETA before the
# job finishes — not a hard guarantee, just a "here's roughly what to expect."
ESTIMATED_SECONDS_PER_FILE = 9


# Issues that are just a prose restatement of what the static linters (flake8/
# pylint/bandit/eslint) already report mechanically, with exact line numbers,
# in `lint_issues` — the AI shouldn't spend its issue budget re-deriving these,
# and a developer gets nothing from a vague sentence a linter already told them.
_NOISE_ISSUE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        # Import-resolution claims are almost always a false positive here:
        # our analyzer environment doesn't have the target repo's own
        # dependencies installed, so any legitimate third-party import can
        # look "broken" to a static tool without actually being broken.
        r"(unable|fails?|failed) to import",
        r"cannot import",
        r"line (is )?too long",
        r"exceeds? (the )?(maximum )?(recommended )?length",
        r"missing (module|class|function|method)?\s*docstring",
        r"unused (import|variable)",
        r"missing type (hint|annotation)",
    ]
]


def _is_noise_issue(issue: dict) -> bool:
    text = f"{issue.get('title', '')} {issue.get('description', '')}"
    return any(p.search(text) for p in _NOISE_ISSUE_PATTERNS)


def _estimate_seconds(files_remaining: int) -> int:
    """Rough ETA shown to the user before/during a scan — not a guarantee,
    just a reasonable expectation based on concurrency and an empirical
    average AI-call duration. Real time varies with provider load and file size."""
    if files_remaining <= 0:
        return 0
    fixed_overhead = 25  # repo intelligence + critical analysis + PR summary calls
    batches = -(-files_remaining // FILE_REVIEW_CONCURRENCY)  # ceil division
    return fixed_overhead + batches * ESTIMATED_SECONDS_PER_FILE


def _calculate_health_score(all_issues: dict) -> dict:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    # Points deducted per individual issue
    deductions = {
        "security":     {"critical": 20, "high": 10, "medium": 4,   "low": 1.5},
        "bugs":         {"critical": 15, "high": 7,  "medium": 2.5, "low": 0.8},
        "performance":  {"critical": 8,  "high": 4,  "medium": 1.5, "low": 0.5},
        # code_quality is noisy — lint style issues are not existential threats
        "code_quality": {"critical": 4,  "high": 1,  "medium": 0.4, "low": 0.1},
    }

    # Hard cap per category: one noisy category cannot sink the whole score
    caps = {
        "security":     40,
        "bugs":         25,
        "performance":  15,
        "code_quality": 15,
    }

    total_deduction = 0.0
    for category, issues in all_issues.items():
        cat_ded = deductions.get(category, {"critical": 4, "high": 1, "medium": 0.4, "low": 0.1})
        cap = caps.get(category, 15)
        cat_total = 0.0
        for issue in issues:
            sev = issue.get("severity") or "low"
            if sev in counts:
                counts[sev] += 1
            d = cat_ded.get(sev, 0.1)
            # accumulate but never exceed the category cap
            cat_total = min(cat_total + d, cap)
        total_deduction += cat_total

    log.debug(
        "Health deduction breakdown: total=%.1f  (sec=%.1f  bugs=%.1f  perf=%.1f  quality=%.1f)",
        total_deduction,
        min(sum(deductions["security"].get(i.get("severity") or "low", 0) for i in all_issues.get("security",[])), caps["security"]),
        min(sum(deductions["bugs"].get(i.get("severity") or "low", 0) for i in all_issues.get("bugs",[])), caps["bugs"]),
        min(sum(deductions["performance"].get(i.get("severity") or "low", 0) for i in all_issues.get("performance",[])), caps["performance"]),
        min(sum(deductions["code_quality"].get(i.get("severity") or "low", 0) for i in all_issues.get("code_quality",[])), caps["code_quality"]),
    )
    return {"score": max(0, round(100 - total_deduction)), "severity_counts": counts}


# ---------------------------------------------------------------------------
# Existing endpoint — unchanged, GitHub Actions uses this
# ---------------------------------------------------------------------------
@app.post("/review", response_model=ReviewResponse)
def review_code(req: ReviewRequest):
    log.info("/review  file=%s  code_len=%d", req.filename, len(req.code))
    ai_result = ai.generate_review(req.filename, req.code, req.analysis)
    if isinstance(ai_result, str):
        try:
            ai_result = json.loads(ai_result)
        except Exception:
            log.error("/review  AI returned unparseable JSON for %s", req.filename)
            return {
                "issues": [],
                "patch": "",
                "patched_code": req.code,
                "success": False,
                "error": "AI returned invalid JSON",
            }
    validated = validate_ai_output(ai_result)
    applied = safe_apply_patch(req.code, validated["patch"])
    log.info(
        "/review done  issues=%d  patch_applied=%s",
        len(validated["issues"]), applied["success"],
    )
    return {
        "issues": validated["issues"],
        "patch": validated["patch"],
        "patched_code": applied["patched_code"],
        "success": applied["success"],
        "error": applied["error"],
    }


# ---------------------------------------------------------------------------
# Full repository analysis — async job + polling, for the React dashboard
# ---------------------------------------------------------------------------
async def _process_single_file(f: dict, semaphore: asyncio.Semaphore, client: httpx.AsyncClient) -> dict:
    async with semaphore:
        analysis = await asyncio.to_thread(analyze_file, f["filepath"])

        ai_result = await repo_reviewer.review_file_enhanced_async(
            f["filename"], f["content"], analysis, client
        )

        file_issues = ai_result.get("issues", [])
        noise_count = sum(1 for i in file_issues if _is_noise_issue(i))
        if noise_count:
            log.info("  dropping %d lint-duplicate issue(s) for %s", noise_count, f["filename"])
            file_issues = [i for i in file_issues if not _is_noise_issue(i)]
        for issue in file_issues:
            issue["filename"] = f["filename"]

        patch = ai_result.get("patch", "")
        if patch.strip():
            ok, reason = is_meaningful_patch(patch)
            if not ok:
                log.info("  discarding patch for %s: %s", f["filename"], reason)
                patch = ""

        patch_category = classify_patch(f["filename"], patch) if patch.strip() else None
        if patch_category == "comment":
            # A comment/docstring-only diff isn't a real fix — drop it as a
            # patch. The underlying issue's suggested_fix text still surfaces
            # separately, it just doesn't clutter the patch comparison view.
            log.info("  discarding comment-only patch for %s", f["filename"])
            patch = ""
            patch_category = None

        return {
            "filename": f["filename"],
            "issues": file_issues,
            "patch": patch,
            "patch_category": patch_category,
        }


async def _run_analysis_job(analysis_id: str, repo_url: str, branch: str = None) -> None:
    t_start = time.perf_counter()
    log.info("[%s] CLONING  %s", analysis_id, repo_url)

    # Cloning is network-bound (can legitimately take 1s or 30s+ depending on
    # GitHub/network conditions) — it happens here, inside the background
    # task, specifically so it's never on the critical path of the HTTP
    # request the frontend is waiting on with a fixed client-side timeout.
    scan = await asyncio.to_thread(scan_repo, repo_url, branch)
    if not scan["success"]:
        log.error("[%s] ANALYSIS ABORTED  reason: %s", analysis_id, scan.get("error"))
        await jobs.set_failed(analysis_id, scan.get("error", "Failed to clone repository"))
        return

    temp_dir = scan["temp_dir"]
    files = scan["files"]
    total_files = len(files)

    await jobs.set_scan_complete(
        analysis_id, scan["file_inventory"], scan["total_files_found"], total_files, scan["resolved_ref"]
    )

    log.info("=" * 60)
    log.info("ANALYSIS START  id=%s  %s  files=%d", analysis_id, repo_url, total_files)
    log.info("=" * 60)

    try:
        t2 = time.perf_counter()
        repo_intel = await asyncio.to_thread(
            repo_reviewer.generate_repo_intelligence, files, scan.get("file_inventory")
        )
        log.info("[%s] repo_intelligence done  %.1fs", analysis_id, time.perf_counter() - t2)

        semaphore = asyncio.Semaphore(FILE_REVIEW_CONCURRENCY)
        file_results: list = [None] * total_files
        done_count = 0
        progress_lock = asyncio.Lock()

        async with httpx.AsyncClient() as client:
            async def _run(idx: int, f: dict):
                nonlocal done_count
                try:
                    result = await asyncio.wait_for(
                        _process_single_file(f, semaphore, client), timeout=FILE_TIMEOUT_SECONDS
                    )
                except asyncio.TimeoutError:
                    log.error(
                        "[%s]  %s exceeded %ds — skipping so the rest of the job can finish",
                        analysis_id, f["filename"], FILE_TIMEOUT_SECONDS,
                    )
                    result = {"filename": f["filename"], "issues": [], "patch": "", "patch_category": None}
                except Exception as exc:
                    log.error("[%s]  %s crashed: %s", analysis_id, f["filename"], exc)
                    result = {"filename": f["filename"], "issues": [], "patch": "", "patch_category": None}

                file_results[idx] = result
                async with progress_lock:
                    done_count += 1
                    await jobs.update_progress(analysis_id, done_count, total_files, f["filename"])
                log.info(
                    "[%s]  [%d/%d] done  %s  issues=%d",
                    analysis_id, done_count, total_files, f["filename"], len(result["issues"]),
                )

            # A single file's timeout/crash is already contained above and never
            # propagates, but gather still needs return_exceptions as a last
            # line of defense — one file must never be able to fail the whole job.
            await asyncio.gather(*(_run(idx, f) for idx, f in enumerate(files)), return_exceptions=True)

        all_issues: dict = {"security": [], "performance": [], "bugs": [], "code_quality": []}
        for idx, result in enumerate(file_results):
            if result is None:
                # Should be unreachable — every _run() path sets this — but
                # never let one missing entry crash the whole job's summary.
                result = file_results[idx] = {
                    "filename": files[idx]["filename"], "issues": [], "patch": "", "patch_category": None,
                }
            for issue in result["issues"]:
                cat = issue.get("category", "code_quality")
                all_issues.get(cat, all_issues["code_quality"]).append(issue)

        health = _calculate_health_score(all_issues)
        sc = health["severity_counts"]
        log.info(
            "[%s] health_score=%d  critical=%d  high=%d  medium=%d  low=%d",
            analysis_id, health["score"], sc["critical"], sc["high"], sc["medium"], sc["low"],
        )

        pr_sum = await asyncio.to_thread(
            repo_reviewer.generate_pr_summary, all_issues, total_files, repo_intel
        )
        critical_analysis = await asyncio.to_thread(
            repo_reviewer.generate_critical_analysis, all_issues, repo_intel, total_files
        )

        total_elapsed = time.perf_counter() - t_start
        log.info("=" * 60)
        log.info(
            "ANALYSIS COMPLETE  id=%s  %.1fs  score=%d  files=%d  issues=%d",
            analysis_id, total_elapsed, health["score"], total_files,
            sum(len(v) for v in all_issues.values()),
        )
        log.info("=" * 60)

        await jobs.set_result(analysis_id, {
            "repo_url": repo_url,
            "health_score": health["score"],
            "files_analyzed": total_files,
            "total_files_found": scan["total_files_found"],
            "repository_intelligence": repo_intel,
            "issues": all_issues,
            "severity_counts": health["severity_counts"],
            "pr_summary": {
                "files_analyzed": total_files,
                "critical_risks": health["severity_counts"]["critical"],
                "main_findings": pr_sum.get("main_findings", ""),
                "recommendation": pr_sum.get("recommendation", "request_changes"),
                "recommendation_reason": pr_sum.get("recommendation_reason", ""),
            },
            "critical_analysis": critical_analysis,
            "file_results": file_results,
        })
    except Exception as exc:
        log.exception("ANALYSIS CRASHED  id=%s  after %.1fs: %s", analysis_id, time.perf_counter() - t_start, exc)
        await jobs.set_failed(analysis_id, str(exc))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        log.info("[%s] temp dir cleaned up: %s", analysis_id, temp_dir)


@app.post("/analyze-repo")
@limiter.limit("5/hour")
async def analyze_repository(request: Request, req: RepoAnalysisRequest, background_tasks: BackgroundTasks):
    log.info("Starting analysis job  repo=%s", req.repo_url)
    analysis_id = await jobs.create_job(req.repo_url, req.branch)
    background_tasks.add_task(_run_analysis_job, analysis_id, req.repo_url, req.branch)
    # No clone/scan here — this must return near-instantly regardless of how
    # slow GitHub/network is at this moment. Poll /analysis/{id}/status for
    # file_inventory (arrives once cloning finishes) and progress.
    return {"analysis_id": analysis_id}


@app.get("/analysis/{analysis_id}/status")
async def get_analysis_status(analysis_id: str, response: Response):
    # This URL is polled repeatedly with an unchanged path while status
    # changes underneath it — make sure no browser/proxy cache ever serves a
    # stale snapshot instead of hitting the job store fresh each time.
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"

    job = await jobs.get_job(analysis_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis not found or expired")
    progress = job["progress"]
    remaining = max(0, progress["total"] - progress["done"])
    return {
        "analysis_id": analysis_id,
        "status": job["status"],  # "cloning" | "running" | "complete" | "failed"
        "file_inventory": job.get("file_inventory"),  # null while still cloning
        "total_files_found": job.get("total_files_found"),
        "progress": progress,
        "estimated_seconds_remaining": (
            _estimate_seconds(remaining) if job["status"] in ("cloning", "running") else 0
        ),
        "error": job.get("error"),
    }


@app.get("/analysis/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    job = await jobs.get_job(analysis_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis not found or expired")
    if job["status"] != "complete":
        raise HTTPException(status_code=409, detail=f"Analysis is {job['status']}, not complete yet")
    return job["result"]


@app.post("/analysis/{analysis_id}/chat")
async def chat_with_analysis(analysis_id: str, payload: dict):
    message = (payload.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    job = await jobs.get_job(analysis_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis not found or expired")
    if job["status"] != "complete":
        raise HTTPException(status_code=409, detail="Analysis isn't complete yet")

    await jobs.append_chat_turn(analysis_id, "user", message)
    answer = await chat.answer_question(job, message, repo_reviewer)
    await jobs.append_chat_turn(analysis_id, "assistant", answer)
    return {"answer": answer}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "PR Guardian AI is running"}


# ---------------------------------------------------------------------------
# Local file review — testing only
# ---------------------------------------------------------------------------
@app.post("/review-file")
def review_file(payload: dict):
    filepath = payload.get("filepath")
    if not filepath:
        raise HTTPException(status_code=400, detail="filepath missing")
    log.info("/review-file  path=%s", filepath)
    try:
        analysis = analyze_file(filepath)
        with open(filepath, "r") as f:
            code = f.read()
        ai_result = ai.generate_review(filepath, code, analysis)
        validated = validate_ai_output(ai_result)
        patched = safe_apply_patch(code, validated["patch"])
        return {
            "analysis": analysis,
            "issues": validated["issues"],
            "patch": validated["patch"],
            "patched_code": patched["patched_code"],
            "success": patched["success"],
            "error": patched.get("error"),
        }
    except Exception as exc:
        log.error("/review-file FAILED: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
