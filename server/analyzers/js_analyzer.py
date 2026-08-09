import difflib

from .common import run_command


def analyze_js(file_path: str):
    output = {
        "language": "javascript",
        "lint_issues": [],
        "security_issues": [],
        "format_suggestions": "",
        "raw_output": "",
        "errors": [],
    }

    # --- ESLint ---
    eslint_cmd = ["eslint", file_path, "-f", "compact"]
    eslint_out, eslint_err = run_command(eslint_cmd)
    if eslint_out:
        output["lint_issues"].extend(eslint_out.splitlines())
    if eslint_err:
        output["errors"].append(f"eslint error: {eslint_err}")

    # --- Prettier diff ---
    # Read-only: never pass --write here. This runs against whatever file_path
    # points to — for /review-file that's a real path on the server's own
    # filesystem, not a throwaway clone, so writing back would silently mutate
    # a file the caller never asked us to change.
    prettier_cmd = ["prettier", "--check", file_path]
    prettier_out, prettier_err = run_command(prettier_cmd)
    if "Code style issues found" in prettier_out:
        formatted, format_err = run_command(["prettier", file_path])
        if formatted and not format_err:
            try:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    original = f.read()
                diff = difflib.unified_diff(
                    original.splitlines(keepends=True),
                    formatted.splitlines(keepends=True),
                    fromfile=file_path,
                    tofile=f"{file_path} (formatted)",
                )
                output["format_suggestions"] = "".join(diff)
            except OSError as exc:
                output["errors"].append(f"prettier diff error: {exc}")

    output["raw_output"] = {"eslint": eslint_out, "prettier": prettier_out}

    return output
