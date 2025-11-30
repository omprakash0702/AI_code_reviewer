from .common import run_command
import json

def analyze_python(file_path: str):
    output = {
        "language": "python",
        "lint_issues": [],
        "security_issues": [],
        "format_suggestions": "",
        "raw_output": "",
        "errors": []
    }

    # --- flake8 lint ---
    flake8_out, flake8_err = run_command(["flake8", file_path])
    if flake8_out:
        output["lint_issues"].extend(flake8_out.splitlines())
    if flake8_err:
        output["errors"].append(f"flake8 error: {flake8_err}")

    # --- pylint logic checks ---
    pylint_out, pylint_err = run_command(["pylint", file_path, "-rn", "-sn"])
    if pylint_out:
        output["lint_issues"].extend(pylint_out.splitlines())
    if pylint_err:
        output["errors"].append(f"pylint error: {pylint_err}")

    # --- bandit security checks ---
    bandit_out, bandit_err = run_command(["bandit", "-q", file_path])
    if bandit_out:
        output["security_issues"].extend(bandit_out.splitlines())
    if bandit_err:
        output["errors"].append(f"bandit error: {bandit_err}")

    # --- black formatting suggestions ---
    black_cmd = ["black", "--diff", "--color", file_path]
    black_out, black_err = run_command(black_cmd)
    if black_out:
        output["format_suggestions"] = black_out
    if black_err:
        output["errors"].append(f"black error: {black_err}")

    output["raw_output"] = {
        "flake8": flake8_out,
        "pylint": pylint_out,
        "bandit": bandit_out,
        "black": black_out
    }

    return output
