from server.diff.validate_patch import (
    is_meaningful_patch,
    is_noop_patch,
    validate_patch_format,
)


def test_empty_patch():
    ok, msg = validate_patch_format("")
    assert not ok


def test_missing_hunk_markers():
    ok, msg = validate_patch_format("this is not a diff at all")
    assert not ok


def test_valid_patch_without_file_headers():
    # AI-generated patches intentionally omit --- / +++ headers (see repo_reviewer.py
    # prompt) — format validation must not require them.
    patch = "@@ -1 +1 @@\n-print(1)\n+print(2)\n"
    ok, msg = validate_patch_format(patch)
    assert ok


def test_noop_patch_same_content_reordered():
    patch = "@@ -1,2 +1,2 @@\n-a\n-b\n+b\n+a\n"
    assert is_noop_patch(patch) is True


def test_noop_patch_with_whitespace_differences():
    patch = "@@ -1 +1 @@\n-  x = 1\n+x = 1\n"
    assert is_noop_patch(patch) is True


def test_real_patch_is_not_noop():
    patch = '@@ -1 +1 @@\n-password = "admin123"\n+password = os.getenv("PASSWORD", "")\n'
    assert is_noop_patch(patch) is False


def test_is_meaningful_patch_rejects_empty():
    ok, reason = is_meaningful_patch("")
    assert not ok
    assert reason == "Empty patch"


def test_is_meaningful_patch_rejects_noop():
    patch = "@@ -1 +1 @@\n-a\n+a\n"
    ok, reason = is_meaningful_patch(patch)
    assert not ok
    assert "no-op" in reason


def test_is_meaningful_patch_accepts_real_fix():
    patch = '@@ -1 +1 @@\n-password = "admin123"\n+password = os.getenv("PASSWORD", "")\n'
    ok, reason = is_meaningful_patch(patch)
    assert ok
    assert reason == ""
