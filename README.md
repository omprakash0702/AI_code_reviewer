AI Code Reviewer

Lightweight, production-ready AI-powered code review system that analyzes code, reports issues, and generates safe unified-diff patches using an LLM.
Includes static analyzers, a safe patch application layer, a simple UI, and CI-ready test suite — perfect for a resume/demo.

Demo screenshot

(Will be transformed to a public URL during deployment)


Key Features

✅ AI-driven code review (OpenAI) — structured JSON output with issues + unified-diff patch

✅ Static analyzers for Python & JS (flake8, pylint, eslint, prettier integration)

✅ Patch safety layer — validates and safely applies patches (no destructive changes)

✅ FastAPI backend with /review and /review-file endpoints

✅ Simple Flask frontend for local demos (within the same repo)

✅ Unit + integration tests (pytest) and CI-ready workflows

✅ GitHub Actions friendly — can comment on PRs and optionally create auto-fix PRs

Repo layout
aicodereviewer/
├── server/                # FastAPI backend (server.app)
│   ├── ai/                # AISuggester, validation
│   ├── analyzers/         # python/js analyzers
│   ├── diff/              # safe_apply, patch utilities
│   ├── schemas/           # pydantic request/response schemas
│   └── app.py
├── web/                   # Simple Flask UI (templates + static)
├── tests/                 # pytest unit + integration tests
├── docs/                  # API, architecture, config docs
├── .github/workflows/     # CI + PR reviewer workflows
├── requirements.txt
└── LICENSE

Quick start (local)

Assumes Python 3.10+, virtualenv activated, and .env configured.

Install dependencies

pip install -r requirements.txt


Create .env with your OpenAI key:

AI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini
AI_API_URL=https://api.openai.com/v1/chat/completions


Run the FastAPI backend

uvicorn server.app:app --reload


(Optional) Run the simple demo UI

python web/app.py


Visit http://127.0.0.1:5000 (Flask UI) or http://127.0.0.1:8000/docs (FastAPI swagger).

Example requests

POST /review — review raw code

{
  "filename": "example.py",
  "code": "x=1\nprint('hi')\n",
  "analysis": {"lint_issues": []}
}


Response

{
  "issues": [
    {"type":"style","line":1,"message":"Add space around =","confidence":0.9}
  ],
  "patch": "--- a/example.py\n+++ b/example.py\n@@ -1 +1 @@\n-x=1\n+ x = 1\n",
  "patched_code": " x = 1\nprint('hi')\n",
  "success": true,
  "error": null
}

Running tests

Run unit + integration tests:

pytest -q


Expected on a properly configured environment:

4 passed, 4 skipped


CI will run the same test suite on push/pull requests.

CI / GitHub Actions

Example workflows included:

.github/workflows/ci.yml — installs deps, runs pytest

.github/workflows/ai-code-review.yml — runs on PRs and can call your /review endpoint to comment with findings; optionally create an auto-fix branch and PR.


Config (docs/config.md)

Important environment variables:

AI_API_KEY — OpenAI API key (required for live AI calls)

AI_MODEL — default gpt-4o-mini

AI_API_URL — default https://api.openai.com/v1/chat/completions

Place them in a .env file at repo root for local development (the code uses python-dotenv).

Security & safety notes

The patch validator enforces unified-diff formatting and basic safety checks before applying patches.

In CI you should disable auto-apply for forks (already included in the example workflow) to avoid malicious PRs auto-merging fixes.

Deployment options

HuggingFace Spaces — fast and free for small demos (works with FastAPI + static UI)

Render / Railway — simple deployment for both backend and frontend

Docker — create a Dockerfile for production containerization

Contribution guidelines

Run tests locally before opening a PR.

Keep changes small and add/update tests for new behavior.

Use descriptive commit messages for PRs.

License

This project is licensed under the MIT License. See LICENSE.

Contact

Maintainer: Your Name — add your email or GitHub profile link here.