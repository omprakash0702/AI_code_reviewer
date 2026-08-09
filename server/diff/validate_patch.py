def validate_patch_format(patch: str):
    """Ensure the diff has at least one hunk marker."""
    if not patch.strip():
        return False, "Empty patch"

    if "@@" not in patch:
        return False, "Patch missing hunk markers"

    return True, ""


def is_noop_patch(patch: str) -> bool:
    """True if the added lines are exactly the removed lines (ignoring order/whitespace) —
    a diff that looks like a change but doesn't actually change anything."""
    removed = []
    added = []
    for line in patch.splitlines():
        if line.startswith("---") or line.startswith("+++") or line.startswith("@@"):
            continue
        if line.startswith("-"):
            removed.append(line[1:].strip())
        elif line.startswith("+"):
            added.append(line[1:].strip())

    if not removed and not added:
        return True

    return sorted(removed) == sorted(added)


def is_meaningful_patch(patch: str):
    """Combined check used before showing a patch to the user."""
    ok, reason = validate_patch_format(patch)
    if not ok:
        return False, reason
    if is_noop_patch(patch):
        return False, "Patch is a no-op (added lines match removed lines)"
    return True, ""
