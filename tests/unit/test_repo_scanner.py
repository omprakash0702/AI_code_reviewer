import json
import tempfile
from pathlib import Path

from server.analyzers.repo_scanner import MAX_FILE_SIZE, MAX_NOTEBOOK_SIZE, scan_files


def _write(root: Path, rel_path: str, content: str = "x = 1\n"):
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scan_files_reviews_any_text_file_not_just_the_old_allowlist():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root, "a.py")
        _write(root, "server.go", "package main\n")
        _write(root, "README.md", "# hello\n")           # used to be excluded — now eligible
        _write(root, "config.yml", "key: value\n")        # used to be excluded — now eligible
        _write(root, "node_modules/dep/index.js", "ignored")  # in IGNORED_DIRS

        files, inventory = scan_files(str(root))

        assert {f["filename"] for f in files} == {"a.py", "server.go", "README.md", "config.yml"}
        assert inventory["total_files"] == 4  # node_modules excluded entirely
        assert inventory["supported"] == 4


def test_scan_files_still_blocks_binaries_and_lockfiles():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root, "a.py")
        (root / "package-lock.json").write_text('{"lockfileVersion": 3}', encoding="utf-8")
        (root / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
        (root / "app.min.js").write_text("!function(){}();", encoding="utf-8")

        files, inventory = scan_files(str(root))

        assert {f["filename"] for f in files} == {"a.py"}
        assert inventory["total_files"] == 4
        assert inventory["skipped_unsupported_type"] == 3


def test_scan_files_detects_binary_content_without_a_known_extension():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root, "a.py")
        (root / "mystery_binary").write_bytes(b"\x00\x01\x02\x03garbage")

        files, inventory = scan_files(str(root))

        assert {f["filename"] for f in files} == {"a.py"}
        assert inventory["skipped_unsupported_type"] == 1


def test_scan_files_skips_oversized_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root, "big.py", "x = 1\n" * (MAX_FILE_SIZE // 5))

        files, inventory = scan_files(str(root))

        assert files == []
        assert inventory["skipped_oversized"] == 1
        assert inventory["total_files"] == 1
        assert inventory["by_extension"][".py"] == 1


def test_scan_files_extracts_only_code_cells_from_notebooks():
    notebook = {
        "cells": [
            {"cell_type": "markdown", "source": ["# Title\n", "Some prose that isn't code.\n"]},
            {"cell_type": "code", "source": ["import pandas as pd\n", "df = pd.read_csv('x.csv')\n"]},
            {"cell_type": "code", "source": ["print(df.head())\n"]},
        ],
        "metadata": {"kernelspec": {"name": "python3"}},
    }
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root, "analysis.ipynb", json.dumps(notebook))

        files, inventory = scan_files(str(root))

        assert len(files) == 1
        content = files[0]["content"]
        assert "import pandas as pd" in content
        assert "print(df.head())" in content
        # Markdown prose and notebook metadata must not leak into the AI's input
        assert "Some prose that isn't code" not in content
        assert "kernelspec" not in content


def test_scan_files_notebook_gets_a_larger_size_allowance():
    # Notebooks legitimately carry embedded output (plots, etc.) inflating
    # their raw file size well past a normal source file's 60KB limit.
    notebook = {"cells": [{"cell_type": "code", "source": ["x = 1\n"]}]}
    padding = "x" * (MAX_FILE_SIZE + 5000)  # bigger than the normal limit...
    notebook["cells"].append({"cell_type": "markdown", "source": [padding]})
    assert MAX_FILE_SIZE < len(json.dumps(notebook)) < MAX_NOTEBOOK_SIZE

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root, "big.ipynb", json.dumps(notebook))

        files, inventory = scan_files(str(root))

        assert len(files) == 1  # ...but still gets scanned, unlike a normal file this size
