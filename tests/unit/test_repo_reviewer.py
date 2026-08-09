from unittest import mock

from server.ai.repo_reviewer import RepoReviewer


def test_review_prompt_is_shared_between_sync_and_async_paths():
    prompt = RepoReviewer._review_prompt("a.py", "x = 1\nprint(x)", {"lint_issues": []})
    assert "PATCH RULES" in prompt
    assert "code_snippet" in prompt


def test_repo_intelligence_uses_full_file_inventory_not_just_sampled_files():
    # generate_repo_intelligence used to only ever see the handful of files
    # it samples content from — it had no idea the repo has 50 files total,
    # mostly config/docs, if only 1 was sampled. The full inventory closes
    # that gap so "whole project" understanding isn't based on a tiny slice.
    rv = RepoReviewer()
    captured = {}

    def fake_call(self, label, prompt):
        captured["prompt"] = prompt
        return {
            "repo_type": "t", "architecture_summary": "s",
            "important_modules": [], "detected_frameworks": [], "primary_language": "Python",
        }

    with mock.patch.object(RepoReviewer, "_call", fake_call):
        rv.generate_repo_intelligence(
            [{"filename": "a.py", "size": 100, "content": "x=1"}],
            {"total_files": 50, "by_extension": {".py": 30, ".md": 10, ".yml": 10}},
        )

    prompt = captured["prompt"]
    assert "50 files total" in prompt
    assert ".py: 30" in prompt and ".md: 10" in prompt


def test_repo_intelligence_handles_missing_inventory_gracefully():
    rv = RepoReviewer()

    def fake_call(self, label, prompt):
        return {
            "repo_type": "t", "architecture_summary": "s",
            "important_modules": [], "detected_frameworks": [], "primary_language": "Python",
        }

    with mock.patch.object(RepoReviewer, "_call", fake_call):
        result = rv.generate_repo_intelligence([{"filename": "a.py", "size": 100, "content": "x=1"}])

    assert result["repo_type"] == "t"
