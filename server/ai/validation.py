# server/ai/validation.py
from typing import Any, Dict, List, Optional


def normalize_issue(raw_issue: Any) -> Optional[Dict]:
    """
    Convert a raw issue (possibly a string or malformed dict) into a valid issue dict.
    Returns None if the issue cannot be normalized.
    """
    if raw_issue is None:
        return None

    # If the model returned a plain string, wrap it
    if isinstance(raw_issue, str):
        return {
            "type": "general",
            "line": None,
            "message": raw_issue,
            "confidence": 0.5
        }

    # If it's already a dict, pick the fields we need and coerce types
    if isinstance(raw_issue, dict):
        # message required at minimum
        msg = raw_issue.get("message") or raw_issue.get("msg") or raw_issue.get("text")
        if not msg:
            return None

        # line may be int or string; coerce to int or None
        line_raw = raw_issue.get("line", None)
        line = None
        try:
            if isinstance(line_raw, int):
                line = line_raw
            elif isinstance(line_raw, str) and line_raw.isdigit():
                line = int(line_raw)
            else:
                # allow "null" and empty
                line = None
        except Exception:
            line = None

        # confidence -> float 0.0 - 1.0
        try:
            conf = float(raw_issue.get("confidence", 0.5))
            # clamp
            if conf < 0.0:
                conf = 0.0
            if conf > 1.0:
                conf = 1.0
        except Exception:
            conf = 0.5

        return {
            "type": raw_issue.get("type", "style"),
            "line": line,
            "message": str(msg),
            "confidence": conf
        }

    # unknown format
    return None


def validate_ai_output(ai_result: Dict) -> Dict:
    """
    Validate and normalize the AI output dictionary.
    Returns a dict with keys:
      - issues: List[issue dicts]
      - patch: str
    Ensures no crashes even if AI output is slightly malformed.
    """
    if not isinstance(ai_result, dict):
        ai_result = {}

    raw_issues = ai_result.get("issues", [])
    normalized: List[Dict] = []

    # If issues is a single string, make it a list
    if isinstance(raw_issues, str):
        raw_issues = [raw_issues]
    if raw_issues is None:
        raw_issues = []

    # Normalize each issue
    for it in raw_issues:
        issue = normalize_issue(it)
        if issue:
            normalized.append(issue)

    # Ensure at least an empty list
    patch = ai_result.get("patch", "")
    if not isinstance(patch, str):
        try:
            patch = str(patch)
        except Exception:
            patch = ""

    return {
        "issues": normalized,
        "patch": patch
    }
