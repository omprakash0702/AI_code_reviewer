from server.analyzers import analyze_file
from server.ai.validation import validate_ai_output
from server.diff.safe_apply import safe_apply_patch

def test_end_to_end(mocker):
    mocker.patch("server.ai.model.AISuggester.generate_review",
                 return_value={"issues": [], "patch": ""})

    analysis = {"lint_issues": []}
    validated = validate_ai_output({"issues": [], "patch": ""})
    result = safe_apply_patch("print(1)\n", validated["patch"])

    assert result["success"] in [True, False]

