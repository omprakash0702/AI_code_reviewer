import pytest
pytest.skip("validate_patch removed from project", allow_module_level=True)

from server.diff.validate_patch import validate_patch_format

def test_empty_patch():
    ok, msg = validate_patch_format("")
    assert not ok

def test_missing_headers():
    ok, msg = validate_patch_format("@@ bad patch @@")
    assert not ok

def test_valid_patch():
    patch = "--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-print(1)\n+print(2)\n"
    ok, msg = validate_patch_format(patch)
    assert ok
