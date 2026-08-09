from unittest import mock

import server.analyzers.js_analyzer as js_analyzer


def test_js_analyzer_collects_eslint_issues():
    def run_command(cmd):
        if cmd[0] == "eslint":
            return ("file.js: line 1, col 5, Error - prefer-const", "")
        return ("", "")

    with mock.patch.object(js_analyzer, "run_command", run_command):
        result = js_analyzer.analyze_js("file.js")

    assert result["language"] == "javascript"
    assert "prefer-const" in result["lint_issues"][0]


def test_js_analyzer_never_passes_write_flag_to_prettier():
    # Regression test: analyze_js used to run `prettier --write`, which
    # silently rewrites the file being "analyzed" on disk. /review-file
    # passes a real server filesystem path straight through, so this was a
    # read-only endpoint mutating whatever file it was pointed at.
    calls = []

    def run_command(cmd):
        calls.append(cmd)
        if cmd[0] == "eslint":
            return ("", "")
        if "--check" in cmd:
            return ("Code style issues found in the above file(s).", "")
        return ("let x = 1;\n", "")

    with mock.patch.object(js_analyzer, "run_command", run_command):
        with mock.patch("builtins.open", mock.mock_open(read_data="let x=1;\n")):
            result = js_analyzer.analyze_js("file.js")

    assert not any("--write" in cmd for cmd in calls)
    assert "-let x=1;" in result["format_suggestions"]
    assert "+let x = 1;" in result["format_suggestions"]


def test_js_analyzer_no_format_suggestions_when_already_clean():
    def run_command(cmd):
        return ("", "")

    with mock.patch.object(js_analyzer, "run_command", run_command):
        result = js_analyzer.analyze_js("file.js")

    assert result["format_suggestions"] == ""
