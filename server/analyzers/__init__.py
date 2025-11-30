from .python_analyzer import analyze_python
from .js_analyzer import analyze_js

def analyze_file(file_path):
    if file_path.endswith(".py"):
        return analyze_python(file_path)
    if file_path.endswith(".js"):
        return analyze_js(file_path)

    return {
        "language": "unknown",
        "lint_issues": [],
        "security_issues": [],
        "format_suggestions": "",
        "errors": ["Unsupported file type"]
    }
