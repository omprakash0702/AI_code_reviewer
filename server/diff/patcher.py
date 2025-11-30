import difflib

class PatchError(Exception):
    pass


def generate_diff(original: str, modified: str, filename="file"):
    """
    Generate a unified diff between original and modified text.
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}"
    )

    return "".join(diff)


def apply_patch(original_code: str, patch: str):
    """
    Apply a unified diff patch to the original code.
    """

    if not patch.strip():
        raise PatchError("Patch is empty")

    try:
        patched = original_code.splitlines(keepends=True)

        # difflib.restore expects a sequence of delta lines
        # So we convert unified diff into a restorable form
        diff_lines = patch.splitlines(keepends=True)

        result = difflib.restore(diff_lines, 2)
        return "".join(result)

    except Exception as e:
        raise PatchError(f"Failed to apply patch: {e}")
