import json
import shutil
import time

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from server.ai.model import AISuggester
from server.ai.repo_reviewer import RepoReviewer
from server.ai.validation import validate_ai_output
from server.analyzers import analyze_file
from server.analyzers.repo_scanner import scan_repo
from server.diff.safe_apply import safe_apply_patch
from server.logger import get_logger
from server.schemas.repo_analysis import RepoAnalysisRequest
from server.schemas.review_request import ReviewRequest
from server.schemas.review_response import ReviewResponse

log = get_logger("app")

app = FastAPI(title="PR Guardian AI")

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
            sev = issue.get("severity", "low")
            if sev in counts:
                counts[sev] += 1
            d = cat_ded.get(sev, 0.1)
            # accumulate but never exceed the category cap
            cat_total = min(cat_total + d, cap)
        total_deduction += cat_total

    log.debug(
        "Health deduction breakdown: total=%.1f  (sec=%.1f  bugs=%.1f  perf=%.1f  quality=%.1f)",
        total_deduction,
        min(sum(deductions["security"].get(i.get("severity","low"),0) for i in all_issues.get("security",[])), caps["security"]),
        min(sum(deductions["bugs"].get(i.get("severity","low"),0) for i in all_issues.get("bugs",[])), caps["bugs"]),
        min(sum(deductions["performance"].get(i.get("severity","low"),0) for i in all_issues.get("performance",[])), caps["performance"]),
        min(sum(deductions["code_quality"].get(i.get("severity","low"),0) for i in all_issues.get("code_quality",[])), caps["code_quality"]),
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
# New endpoint — full repository analysis for the React dashboard
# ---------------------------------------------------------------------------
@app.post("/analyze-repo")
def analyze_repository(req: RepoAnalysisRequest):
    t_start = time.perf_counter()
    log.info("=" * 60)
    log.info("ANALYSIS START  %s", req.repo_url)
    log.info("=" * 60)

    # ── Step 1: Clone + scan ──────────────────────────────────────
    scan = scan_repo(req.repo_url, req.branch)
    if not scan["success"]:
        log.error("ANALYSIS ABORTED  reason: %s", scan.get("error"))
        raise HTTPException(
            status_code=400,
            detail=scan.get("error", "Failed to clone repository"),
        )

    temp_dir = scan["temp_dir"]
    files = scan["files"]
    log.info(
        "Step 1 done  total_files=%d  analyzing=%d  temp=%s",
        scan["total_files_found"], len(files), temp_dir,
    )

    try:
        # ── Step 2: Repository intelligence ──────────────────────
        t2 = time.perf_counter()
        repo_intel = repo_reviewer.generate_repo_intelligence(files)
        log.info("Step 2 done  repo_intelligence  %.1fs", time.perf_counter() - t2)

        # ── Step 3: Per-file static analysis + AI review ─────────
        all_issues: dict = {
            "security": [],
            "performance": [],
            "bugs": [],
            "code_quality": [],
        }
        file_results = []
        total_files = len(files)

        for idx, f in enumerate(files, start=1):
            log.info("Step 3  [%d/%d]  %s", idx, total_files, f["filename"])
            t_file = time.perf_counter()
            try:
                analysis = analyze_file(f["filepath"])
                lint_count = len(analysis.get("lint_issues", []))
                sec_count = len(analysis.get("security_issues", []))
                log.debug(
                    "  static analysis done  lint=%d  security=%d", lint_count, sec_count
                )

                ai_result = repo_reviewer.review_file_enhanced(
                    f["filename"], f["content"], analysis
                )

                file_issues = ai_result.get("issues", [])
                for issue in file_issues:
                    cat = issue.get("category", "code_quality")
                    issue["filename"] = f["filename"]
                    target = all_issues.get(cat, all_issues["code_quality"])
                    target.append(issue)

                file_results.append({
                    "filename": f["filename"],
                    "issues": file_issues,
                    "patch": ai_result.get("patch", ""),
                })
                log.info(
                    "  [%d/%d] done  issues=%d  time=%.1fs",
                    idx, total_files, len(file_issues), time.perf_counter() - t_file,
                )
            except Exception as exc:
                log.error("  [%d/%d] FAILED %s: %s", idx, total_files, f["filename"], exc)
                continue

        # ── Step 4: Health score ──────────────────────────────────
        health = _calculate_health_score(all_issues)
        sc = health["severity_counts"]
        log.info(
            "Step 4 done  health_score=%d  critical=%d  high=%d  medium=%d  low=%d",
            health["score"], sc["critical"], sc["high"], sc["medium"], sc["low"],
        )

        # ── Step 5: PR summary ────────────────────────────────────
        t5 = time.perf_counter()
        pr_sum = repo_reviewer.generate_pr_summary(all_issues, len(files), repo_intel)
        log.info("Step 5 done  pr_summary  %.1fs", time.perf_counter() - t5)

        total_elapsed = time.perf_counter() - t_start
        log.info("=" * 60)
        log.info(
            "ANALYSIS COMPLETE  %.1fs  score=%d  files=%d  issues=%d",
            total_elapsed, health["score"], len(files),
            sum(len(v) for v in all_issues.values()),
        )
        log.info("=" * 60)

        return {
            "repo_url": req.repo_url,
            "health_score": health["score"],
            "files_analyzed": len(files),
            "total_files_found": scan["total_files_found"],
            "repository_intelligence": repo_intel,
            "issues": all_issues,
            "severity_counts": health["severity_counts"],
            "pr_summary": {
                "files_analyzed": len(files),
                "critical_risks": health["severity_counts"]["critical"],
                "main_findings": pr_sum.get("main_findings", ""),
                "recommendation": pr_sum.get("recommendation", "request_changes"),
                "recommendation_reason": pr_sum.get("recommendation_reason", ""),
            },
            "file_results": file_results,
        }
    except Exception as exc:
        log.exception("ANALYSIS CRASHED after %.1fs: %s", time.perf_counter() - t_start, exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        log.info("Temp dir cleaned up: %s", temp_dir)


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
