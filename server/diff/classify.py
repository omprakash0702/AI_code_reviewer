import os

DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".txt"}

# Extensions whose comment syntax we know how to recognize.
PY_EXTENSIONS = {".py"}
C_STYLE_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp"}


def _is_comment_line(line: str, ext: str):
    """True/False if the line is clearly a comment/non-comment, None if it's blank
    (and therefore uninformative) or the language's comment syntax is unknown."""
    stripped = line.strip()
    if not stripped:
        return None
    if ext in PY_EXTENSIONS:
        return stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''")
    if ext in C_STYLE_EXTENSIONS:
        return stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*") or stripped.endswith("*/")
    return None


def classify_patch(filename: str, patch: str) -> str:
    """Categorize a patch as 'documentation', 'comment', or 'code'.

    - Markdown/doc files are always 'documentation', regardless of diff content.
    - Otherwise, if every changed line is a comment for that language, it's 'comment'.
    - Anything else (including unknown languages, where we can't tell) defaults to 'code'.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext in DOC_EXTENSIONS:
        return "documentation"

    if not patch or not patch.strip():
        return "code"

    changed_lines = []
    for line in patch.splitlines():
        if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
            continue
        if line.startswith("-") or line.startswith("+"):
            changed_lines.append(line[1:])

    verdicts = [_is_comment_line(line, ext) for line in changed_lines]
    verdicts = [v for v in verdicts if v is not None]

    if verdicts and all(verdicts):
        return "comment"
    return "code"
