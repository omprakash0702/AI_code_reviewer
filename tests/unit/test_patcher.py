import pytest
pytest.skip("patcher.py no longer used in project", allow_module_level=True)

from server.diff.patcher import generate_diff, apply_patch, PatchError

def test_generate_diff():
    original = "print('hello')\n"
    updated = "print('hello world')\n"
    diff = generate_diff("test.py", original, updated)
    assert "--- a/test.py" in diff
    assert "+++ b/test.py" in diff
    assert "@@" in diff

def test_apply_valid_patch():
    original = "x = 1\n"
    updated = "x = 2\n"
    diff = generate_diff("a.py", original, updated)
    patched = apply_patch(original, diff)
    assert patched == updated

def test_apply_invalid_patch():
    original = "x = 1\n"
    invalid_patch = "--- missing ---\n"
    try:
        apply_patch(original, invalid_patch)
        assert False  # should not reach
    except PatchError:
        assert True
