import json
import os
import re
import time

import httpx
from dotenv import load_dotenv

from server.logger import get_logger

load_dotenv()

log = get_logger("repo_reviewer")


def _extract_json(raw: str) -> dict:
    for fence in ("```json", "```"):
        if fence in raw:
            raw = raw.split(fence, 1)[1].rsplit("```", 1)[0].strip()
            break
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


class RepoReviewer:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY")
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")
        self.url = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
        log.debug("RepoReviewer ready  model=%s", self.model)

    def _payload(self, prompt: str) -> dict:
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _call(self, label: str, prompt: str) -> dict:
        log.debug("AI call start  [%s]  prompt_len=%d chars", label, len(prompt))
        t0 = time.perf_counter()

        resp = httpx.post(self.url, headers=self._headers(), json=self._payload(prompt), timeout=60)
        elapsed = time.perf_counter() - t0

        log.debug(
            "AI call done   [%s]  status=%d  %.1fs",
            label, resp.status_code, elapsed,
        )

        raw = resp.json()["choices"][0]["message"]["content"]
        log.debug("Raw response length: %d chars", len(raw))

        result = _extract_json(raw)
        log.debug("JSON parse OK  [%s]", label)
        return result

    async def _call_async(self, label: str, prompt: str, client: httpx.AsyncClient) -> dict:
        log.debug("AI call start  [%s]  prompt_len=%d chars", label, len(prompt))
        t0 = time.perf_counter()

        resp = await client.post(self.url, headers=self._headers(), json=self._payload(prompt), timeout=60)
        elapsed = time.perf_counter() - t0

        log.debug(
            "AI call done   [%s]  status=%d  %.1fs",
            label, resp.status_code, elapsed,
        )

        raw = resp.json()["choices"][0]["message"]["content"]
        log.debug("Raw response length: %d chars", len(raw))

        result = _extract_json(raw)
        log.debug("JSON parse OK  [%s]", label)
        return result

    def generate_repo_intelligence(self, files: list, file_inventory: dict = None) -> dict:
        log.info("Generating repository intelligence for %d files…", len(files))
        file_list = "\n".join(
            f"- {f['filename']} ({f['size']} bytes)" for f in files[:30]
        )
        samples = ""
        for f in files[:8]:
            snippet = f["content"][:400]
            samples += f"\n### {f['filename']}\n```\n{snippet}\n```\n"

        inventory_summary = ""
        if file_inventory:
            by_ext = file_inventory.get("by_extension") or {}
            ext_line = ", ".join(f"{ext}: {count}" for ext, count in list(by_ext.items())[:20])
            inventory_summary = (
                f"\nFull repository composition (every file, not just the ones sampled above): "
                f"{file_inventory.get('total_files', '?')} files total. By type: {ext_line}\n"
            )

        prompt = f"""Analyze this repository and return ONLY valid JSON with no extra text.
This is the FIRST step of the review — form a genuine understanding of the
whole project's shape before any individual file gets reviewed one by one.
{inventory_summary}
A sample of the highest-signal files:
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

    @staticmethod
    def _review_prompt(filename: str, code: str, analysis: dict) -> str:
        numbered_code = "\n".join(
            f"{i + 1}: {line}" for i, line in enumerate(code.splitlines())
        )[:2800]
        return f"""You are a senior code reviewer. Return ONLY valid JSON with no extra text.

File: {filename}
```
{numbered_code}
```
(Each line above is prefixed "N: " with its line number for your reference only
— never include that "N: " prefix in code_snippet or suggested_fix, just the
real source code.)

Static analysis: {json.dumps(analysis, default=str)[:800]}

Return this JSON shape:
{{
  "issues": [
    {{
      "category": "security",
      "severity": "critical",
      "title": "Short issue title",
      "description": "One sentence on why this matters",
      "impact": "What could happen if not fixed",
      "line": 42,
      "code_snippet": "the exact current code from the file that has the problem, verbatim, 1-6 lines, preserving original indentation",
      "suggested_fix": "the corrected replacement code for that exact snippet — real code, not a sentence"
    }}
  ],
  "patch": "unified diff or empty string"
}}

code_snippet and suggested_fix are both REAL CODE, copy-pasted/derived directly
from the file above — never a description of what to do. A developer must be
able to see the current code and the fixed code side by side and immediately
understand the change. If you cannot point to a specific line or snippet for
an issue, do not report that issue.

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

PRIORITIZE substance over style: security, bugs, and performance issues always
come before code_quality. Only include a code_quality issue if it reflects a
real structural or maintainability problem — NOT a missing docstring, missing
type hint, or naming nit. If a file has no real security/bug/performance issue
and its only flaws are cosmetic, it is completely fine to return an empty
issues list. A cosmetic-only file is not a failure to find something.

Never report an issue that just restates what a linter already reports
mechanically with a line number — line-too-long, unused imports/variables,
missing docstrings, missing type hints. That data already exists in "Static
analysis" above and is shown to the developer separately; repeating it in
prose adds zero value. Your job is to find what static analysis CANNOT: real
security flaws, logic bugs, race conditions, N+1 queries, broken error
handling, unsafe assumptions — things that require actually understanding
what the code does.

If "Static analysis" above is empty or says no analyzer ran for this file type,
that means our tooling doesn't support this language — it is NOT a defect in the
file. Never report an issue claiming a file extension, config format, or syntax
is "unsupported" or "invalid" based on that alone. Only report issues you can
verify by actually reading the code.

Never report an issue claiming an import "fails", is "unable to be imported",
or that a package "may not be installed" — our static analysis environment
does not have the target repo's own dependencies installed, so a normal
third-party import (e.g. a real package like sqlalchemy or requests used
correctly) can look unresolvable to our tooling without the code being wrong
at all. Assume imports of real, correctly-used packages work — only flag an
import if it's clearly a typo, a wrong relative path, or references a module
that doesn't exist anywhere in this codebase.

PATCH RULES: Include a patch only when you have a concrete, minimal, verifiable
fix for a specific issue you found. The patch must be a standard unified diff
starting with @@ -line,count +line,count @@ markers.
Example:
@@ -5,4 +5,4 @@
 import os
-password = "admin123"
+password = os.getenv("PASSWORD", "")

Do NOT write a patch whose only change is adding, editing, or removing a
comment or docstring — that is never a "fix" worth patching, even if the issue
you reported was about documentation. Patches exist to change behavior or
structure: fix the vulnerability, fix the bug, fix the logic. If the only
thing you can offer is a comment/docstring tweak, leave "patch" empty and put
the suggestion in suggested_fix text instead.

Never emit a patch whose added lines are the same as its removed lines (a no-op
diff that changes nothing) — that wastes the reader's time. If you can't produce
a real, minimal fix, leave "patch" as an empty string and rely on suggested_fix
text instead. Do not fabricate a patch just to have one."""

    def review_file_enhanced(self, filename: str, code: str, analysis: dict) -> dict:
        log.info("AI reviewing  %s  (%d chars)", filename, len(code))
        prompt = self._review_prompt(filename, code, analysis)
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

    async def review_file_enhanced_async(
        self, filename: str, code: str, analysis: dict, client: httpx.AsyncClient
    ) -> dict:
        log.info("AI reviewing  %s  (%d chars)", filename, len(code))
        prompt = self._review_prompt(filename, code, analysis)
        try:
            result = await self._call_async(f"review:{filename}", prompt, client)
            issue_count = len(result.get("issues", []))
            has_patch = bool(result.get("patch", "").strip())
            log.info(
                "  → %s: %d issue(s)  patch=%s",
                filename, issue_count, "yes" if has_patch else "no",
            )
            return result
        except Exception as exc:
            log.error("review_file_enhanced_async FAILED for %s: %s", filename, exc)
            return {"issues": [], "patch": ""}

    def generate_critical_analysis(
        self, all_issues: dict, repo_intel: dict, files_analyzed: int
    ) -> dict:
        flat = []
        for category, issues in all_issues.items():
            for issue in issues:
                flat.append(
                    f"- [{category}/{issue.get('severity','low')}] "
                    f"{issue.get('filename','?')}: {issue.get('title','')}"
                )
        log.info(
            "Generating critical analysis  files=%d  total_issues=%d",
            files_analyzed, len(flat),
        )

        if not flat:
            log.info("No issues found — skipping critical analysis call")
            return {
                "systemic_patterns": [],
                "top_risk": None,
                "priority_recommendations": [],
            }

        issue_list = "\n".join(flat[:150])
        prompt = f"""You are a principal engineer doing a cross-file risk review of an entire
repository — not reviewing one file at a time, but looking for patterns ACROSS
the issues already found. Return ONLY valid JSON with no extra text.

Repo type: {repo_intel.get('repo_type', 'Unknown')}
Files analyzed: {files_analyzed}

All issues found across the repo (category/severity, file, title):
{issue_list}

Return exactly this JSON shape:
{{
  "systemic_patterns": [
    {{
      "pattern": "Short name for a pattern that repeats across multiple files (e.g. 'Missing input validation on API boundaries')",
      "category": "security",
      "severity": "critical",
      "affected_files": ["file1.py", "file2.py"],
      "why_it_matters": "Why this being systemic (not a one-off) makes it more dangerous than any single instance"
    }}
  ],
  "top_risk": {{
    "title": "The single most critical risk in this repo right now",
    "severity": "critical",
    "description": "What it is and why it's the top priority over everything else found",
    "affected_files": ["file1.py"]
  }},
  "priority_recommendations": [
    {{"priority": 1, "action": "Concrete next step", "reason": "Why this comes first"}}
  ]
}}

Rules:
- Only report a systemic_pattern if the SAME kind of issue genuinely repeats across 2+ files — do not invent patterns from a single occurrence.
- top_risk must be null if there are no critical/high severity issues at all.
- priority_recommendations: at most 5, ordered by actual priority — fix-the-fire-first, not alphabetical.
- Be specific to this repo's actual issues. No generic advice."""
        try:
            result = self._call("critical_analysis", prompt)
            log.info(
                "Critical analysis: %d systemic pattern(s)  top_risk=%r",
                len(result.get("systemic_patterns", [])),
                (result.get("top_risk") or {}).get("title"),
            )
            return result
        except Exception as exc:
            log.error("generate_critical_analysis FAILED: %s", exc)
            return {
                "systemic_patterns": [],
                "top_risk": None,
                "priority_recommendations": [],
            }

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
