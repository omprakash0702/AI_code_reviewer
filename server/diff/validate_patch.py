def validate_patch_format(patch: str):
    """Ensure the diff contains required diff headers."""
    if not patch.strip():
        return False, "Empty patch"

    if "---" not in patch or "+++" not in patch:
        return False, "Patch missing diff headers"

    if "@@" not in patch:
        return False, "Patch missing hunk markers"

    return True, ""
