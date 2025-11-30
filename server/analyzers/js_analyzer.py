from .common import run_command

def analyze_js(file_path: str):
    output = {
        "language": "javascript",
        "lint_issues": [],
        "security_issues": [],
        "format_suggestions": "",
        "raw_output": "",
        "errors": []
    }

    # --- ESLint ---
    eslint_cmd = ["eslint", file_path, "-f", "compact"]
    eslint_out, eslint_err = run_command(eslint_cmd)
    if eslint_out:
        output["lint_issues"].extend(eslint_out.splitlines())
    if eslint_err:
        output["errors"].append(f"eslint error: {eslint_err}")

    # --- Prettier diff ---
    prettier_cmd = ["prettier", "--check", file_path]
    prettier_out, prettier_err = run_command(prettier_cmd)
    if "Code style issues found" in prettier_out:
        format_cmd = ["prettier", "--write", "--list-different", file_path]
        diff_out, diff_err = run_command(format_cmd)
        output["format_suggestions"] = diff_out

    output["raw_output"] = {
        "eslint": eslint_out,
        "prettier": prettier_out
    }

    return output
