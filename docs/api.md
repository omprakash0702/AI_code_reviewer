📘 AI Code Reviewer — API Documentation

Base URL (Local):

http://127.0.0.1:8000


This API allows you to:

Submit source code

Receive AI-generated review issues

Get a safe unified diff patch

Get auto-patched code

✅ 1. Health Check
GET /

Used to verify that the API server is running.

Request
GET /

Response (200)
{
  "status": "ok",
  "message": "AI Code Reviewer API is running"
}

✅ 2. Review Code (Main Endpoint)
POST /review

This is the main production endpoint used by:

Web UI

GitHub Actions

External tools

It sends code + static analysis to AI and returns a review + patch.

✅ Request Body
{
  "filename": "test.py",
  "code": "x=1\nprint(\"Hello\")",
  "analysis": {
    "lint_issues": []
  }
}

Field Explanation
Field	Type	Description
filename	string	Name of the source file
code	string	Full code as a string
analysis	object	Output from static analyzers
✅ Successful Response (200)
{
  "issues": [
    {
      "type": "style",
      "line": 1,
      "message": "Spacing around assignment operator is missing.",
      "confidence": 0.9
    }
  ],
  "patch": "--- a/test.py\n+++ b/test.py\n@@ -1,2 +1,2 @@\n- x=1\n+ x = 1\n",
  "patched_code": "x = 1\nprint(\"Hello\")\n",
  "success": true,
  "error": null
}

✅ Response Fields
Field	Type	Description
issues	array	List of problems found by AI
patch	string	Unified diff patch
patched_code	string	Code after applying patch
success	boolean	Whether patch was applied
error	string/null	Error message if failed
❌ 422 — Validation Error

Occurs when request JSON is invalid.

{
  "detail": [
    {
      "loc": ["body", 0],
      "msg": "JSON decode error",
      "type": "json_invalid"
    }
  ]
}

❌ 500 — Server Error

Occurs when AI returns invalid output.

{
  "detail": "AI returned invalid JSON"
}

✅ 3. Review File (Local Testing Only)
POST /review-file

Used for local backend testing. Reads file directly from disk.

Request Body
{
  "filepath": "example.py"
}

Response
{
  "analysis": {
    "lint_issues": []
  },
  "issues": [],
  "patch": "",
  "patched_code": "",
  "success": false,
  "error": "Empty patch"
}

✅ 4. Curl Example
curl -X POST http://127.0.0.1:8000/review \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "bad_code.py",
    "code": "x=1\nprint(\"Hello\")",
    "analysis": {"lint_issues": []}
  }'

✅ 5. Swagger / OpenAPI UI

You can fully test the API here:

http://127.0.0.1:8000/docs

✅ 6. Notes

The API always returns valid JSON.

The patch is always in GNU unified diff format.

AI model and API key are configurable via .env.

This API is suitable for:

GitHub CI/CD

Web UI

External automation