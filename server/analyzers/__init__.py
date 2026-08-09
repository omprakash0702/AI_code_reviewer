from .js_analyzer import analyze_js
from .python_analyzer import analyze_python


def analyze_file(file_path):
    if file_path.endswith(".py"):
        return analyze_python(file_path)
    if file_path.endswith(".js"):
        return analyze_js(file_path)

    # No static analyzer wired up for this extension (.ts, .tsx, .jsx, .java, etc).
    # This is NOT a problem with the file — don't frame it as an "error", or the
    # AI reviewer downstream will mistake "we can't lint this" for "this file is broken".
    return {
        "language": "unsupported",
        "lint_issues": [],
        "security_issues": [],
        "format_suggestions": "",
        "errors": [],
        "note": "No static analyzer available for this file type — AI review relies on reading the code directly.",
    }
