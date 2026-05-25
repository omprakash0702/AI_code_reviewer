import json
import os
import time

import httpx
from dotenv import load_dotenv

from server.logger import get_logger

load_dotenv()

log = get_logger("repo_reviewer")


class RepoReviewer:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY")
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")
        self.url = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
        log.debug("RepoReviewer ready  model=%s", self.model)

    def _call(self, label: str, prompt: str) -> dict:
        log.debug("AI call start  [%s]  prompt_len=%d chars", label, len(prompt))
        t0 = time.perf_counter()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        resp = httpx.post(self.url, headers=headers, json=payload, timeout=60)
        elapsed = time.perf_counter() - t0

        log.debug(
            "AI call done   [%s]  status=%d  %.1fs",
            label, resp.status_code, elapsed,
        )

        raw = resp.json()["choices"][0]["message"]["content"]
        log.debug("Raw response length: %d chars", len(raw))

        for fence in ("```json", "```"):
            if fence in raw:
                raw = raw.split(fence, 1)[1].rsplit("```", 1)[0].strip()
                log.debug("Stripped markdown fence from response")
                break

        result = json.loads(raw)
        log.debug("JSON parse OK  [%s]", label)
        return result

    def generate_repo_intelligence(self, files: list) -> dict:
        log.info("Generating repository intelligence for %d files…", len(files))
        file_list = "\n".join(
            f"- {f['filename']} ({f['size']} bytes)" for f in files[:30]
        )
        samples = ""
        for f in files[:4]:
            snippet = f["content"][:400]
            samples += f"\n### {f['filename']}\n```\n{snippet}\n```\n"

        prompt = f"""Analyze this repository and return ONLY valid JSON with no extra text.

Files:
{file_list}

Code samples:{samples}

Return exactly this JSON shape:
{{
  "repo_type": "e.g. FastAPI REST API or React Web App",
  "architecture_summary": "2-3 sentence description of architecture",
  "important_modules": ["module1", "module2", "module3"],
  "detected_frameworks": ["fw1", "fw2"],
  "primary_language": "Python or JavaScript etc",
  "ai_insights": [
    "One specific architectural observation or risk (e.g. 'Heavy LangChain dependency creates tight coupling')",
    "One complexity or design note (e.g. 'Agent graph structure increases cognitive overhead')",
    "One actionable improvement (e.g. 'Cache repeated LLM calls to reduce latency')",
    "One strength or notable pattern (e.g. 'Clear separation between retrieval and generation layers')"
  ]
}}

For ai_insights: write exactly 4 concrete, specific bullets about THIS repo. No generic advice."""
        try:
            result = self._call("repo_intelligence", prompt)
            log.info(
                "Repo intelligence: type=%r  lang=%s  frameworks=%s",
                result.get("repo_type"),
                result.get("primary_language"),
                result.get("detected_frameworks"),
            )
            return result
        except Exception as exc:
            log.error("repo_intelligence FAILED: %s", exc)
            return {
                "repo_type": "Unknown",
                "architecture_summary": "Unable to analyze architecture.",
                "important_modules": [],
                "detected_frameworks": [],
                "primary_language": "Unknown",
            }

    def review_file_enhanced(self, filename: str, code: str, analysis: dict) -> dict:
        log.info("AI reviewing  %s  (%d chars)", filename, len(code))
        prompt = f"""You are a senior code reviewer. Return ONLY valid JSON with no extra text.

File: {filename}
```
{code[:2500]}
```
Static analysis: {json.dumps(analysis, default=str)[:800]}

Return this JSON shape:
{{
  "issues": [
    {{
      "category": "security",
      "severity": "critical",
      "title": "Short issue title",
      "description": "Why this matters",
      "impact": "What could happen if not fixed",
      "suggested_fix": "Concrete actionable fix",
      "line": null
    }}
  ],
  "patch": "unified diff or empty string"
}}

Category must be one of: security, performance, bugs, code_quality

Severity guide — be CONSERVATIVE, most issues are medium or low:
  security:
    critical = exploitable vulnerability (SQLi, RCE, hardcoded secret exposed)
    high     = missing auth check, unsafe deserialization, weak crypto in use
    medium   = input not validated at boundary, overly broad CORS/permissions
    low      = minor info leak, debug endpoint left open
  bugs:
    critical = guaranteed crash or data corruption in normal execution
    high     = exception swallowed, wrong conditional leads to wrong output
    medium   = edge case not handled, possible None dereference
    low      = off-by-one in non-critical path
  performance:
    critical = O(n^2) or worse in a hot loop, unbounded memory growth
    high     = synchronous blocking call inside async handler, N+1 query
    medium   = unnecessary repeated computation, missing cache
    low      = minor inefficiency with negligible real-world impact
  code_quality:
    critical = unrecoverable design flaw making the module untestable/unusable
    high     = no error handling on ALL external I/O calls, function >80 lines with no structure
    medium   = complex logic with no comments, misleading variable name
    low      = missing type hint, long line, style nit, missing docstring

Return at most 5 issues total. Only report issues that actually matter. Do not
report every lint warning as high severity.

PATCH REQUIREMENT: If you find any security, bug, or performance issue — you MUST include a patch.
The patch must be a standard unified diff starting with @@ -line,count +line,count @@ markers.
Example:
@@ -5,4 +5,4 @@
 import os
-password = "admin123"
+password = os.getenv("PASSWORD", "")

If no issues warrant a patch, return empty string."""
        try:
            result = self._call(f"review:{filename}", prompt)
            issue_count = len(result.get("issues", []))
            has_patch = bool(result.get("patch", "").strip())
            log.info(
                "  → %s: %d issue(s)  patch=%s",
                filename, issue_count, "yes" if has_patch else "no",
            )
            return result
        except Exception as exc:
            log.error("review_file_enhanced FAILED for %s: %s", filename, exc)
            return {"issues": [], "patch": ""}

    def generate_pr_summary(
        self, all_issues: dict, files_analyzed: int, repo_intel: dict
    ) -> dict:
        counts = {cat: len(issues) for cat, issues in all_issues.items()}
        critical = sum(
            1
            for issues in all_issues.values()
            for i in issues
            if i.get("severity") == "critical"
        )
        log.info(
            "Generating PR summary  files=%d  critical=%d  sec=%d  perf=%d  bugs=%d  quality=%d",
            files_analyzed, critical,
            counts.get("security", 0), counts.get("performance", 0),
            counts.get("bugs", 0), counts.get("code_quality", 0),
        )
        prompt = f"""Write a concise PR review summary. Return ONLY valid JSON.

Repo type: {repo_intel.get('repo_type', 'Unknown')}
Files analyzed: {files_analyzed}
Issues — security: {counts.get('security', 0)}, performance: {counts.get('performance', 0)}, bugs: {counts.get('bugs', 0)}, code_quality: {counts.get('code_quality', 0)}
Critical issues: {critical}

Return:
{{
  "main_findings": "2-3 sentence summary of the most important findings",
  "recommendation": "approve",
  "recommendation_reason": "One sentence explaining the recommendation"
}}

Set recommendation to "request_changes" if critical > 0 or security issues exist, otherwise "approve"."""
        try:
            result = self._call("pr_summary", prompt)
            log.info("PR recommendation: %s", result.get("recommendation"))
            return result
        except Exception as exc:
            log.error("generate_pr_summary FAILED: %s", exc)
            rec = "request_changes" if critical > 0 else "approve"
            return {
                "main_findings": "Analysis complete.",
                "recommendation": rec,
                "recommendation_reason": "Based on automated issue analysis.",
            }
