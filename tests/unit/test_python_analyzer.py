from unittest import mock

import server.analyzers.python_analyzer as python_analyzer


def _mock_run_command(responses):
    def run_command(cmd):
        return responses.get(cmd[0], ("", ""))
    return run_command


def test_python_analyzer_collects_lint_and_security_issues():
    responses = {
        "flake8": ("file.py:1:1: E501 line too long", ""),
        "pylint": ("file.py:2:0: C0114: Missing module docstring", ""),
        "bandit": (">> Issue: [B105:hardcoded_password_string]", ""),
        "black": ("", ""),
    }
    with mock.patch.object(python_analyzer, "run_command", _mock_run_command(responses)):
        result = python_analyzer.analyze_python("file.py")

    assert result["language"] == "python"
    assert "E501 line too long" in result["lint_issues"][0]
    assert "Missing module docstring" in result["lint_issues"][1]
    assert "hardcoded_password_string" in result["security_issues"][0]
    assert result["errors"] == []


def test_python_analyzer_black_diff_has_no_ansi_codes():
    # Regression test: black used to be invoked with --color, leaking raw
    # ANSI escape codes into format_suggestions (which flows into AI prompts
    # and the JSON API response).
    responses = {
        "flake8": ("", ""),
        "pylint": ("", ""),
        "bandit": ("", ""),
        "black": ("--- a\n+++ b\n@@ -1 +1 @@\n-x=1\n+x = 1\n", ""),
    }
    with mock.patch.object(python_analyzer, "run_command", _mock_run_command(responses)):
        result = python_analyzer.analyze_python("file.py")

    assert "\x1b[" not in result["format_suggestions"]
    assert "x = 1" in result["format_suggestions"]


def test_python_analyzer_surfaces_tool_errors():
    responses = {
        "flake8": ("", "flake8 crashed"),
        "pylint": ("", ""),
        "bandit": ("", ""),
        "black": ("", ""),
    }
    with mock.patch.object(python_analyzer, "run_command", _mock_run_command(responses)):
        result = python_analyzer.analyze_python("file.py")

    assert any("flake8 error" in e for e in result["errors"])
