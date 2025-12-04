AI Code Reviewer & Auto-Fix Tool








An AI-powered Code Review & Auto-Fix Tool that analyzes source code using:

Static analyzers (Flake8, Pylint, Bandit, ESLint)

OpenAI for intelligent review

Safe patch generation using unified diffs

It can be used as:

A local web app

A backend API

A GitHub PR reviewer (CI/CD)

🚀 Features

✅ Detects code quality, style & security issues

✅ Generates safe auto-fix patches

✅ Returns patched code

✅ Works with Python & JavaScript

✅ OpenAI-powered

✅ REST API using FastAPI

✅ Ready for GitHub Actions

✅ Beginner-friendly & resume-ready

🧱 Tech Stack

Backend: FastAPI

AI: OpenAI API

Static Analysis: Flake8, Pylint, Bandit, ESLint

Diff Engine: Unified Diff Patch

Testing: Pytest

Deployment: Local / Render / HuggingFace

📂 Project Structure
aicodereviewer/
├── server/
│   ├── ai/
│   ├── analyzers/
│   ├── diff/
│   ├── schemas/
│   └── app.py
├── tests/
├── docs/
├── LICENSE
├── README.md
├── requirements.txt
└── .env

⚙️ Installation
git clone https://github.com/your-username/aicodereviewer.git
cd aicodereviewer
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt

🔑 Setup Environment

Create a .env file:

AI_API_KEY=your_openai_api_key
AI_MODEL=gpt-4o-mini
AI_API_URL=https://api.openai.com/v1/chat/completions

▶️ Run the Server
uvicorn server.app:app --reload


Open:

http://127.0.0.1:8000/docs

🧪 Example API Call
curl -X POST http://127.0.0.1:8000/review \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "bad_code.py",
    "code": "x=1\nprint(\"Hello\")",
    "analysis": {"lint_issues": []}
  }'

✅ Example Response
{
  "issues": [
    {
      "type": "style",
      "line": 1,
      "message": "Spacing around assignment operator is missing.",
      "confidence": 0.9
    }
  ],
  "patch": "--- a/bad_code.py\n+++ b/bad_code.py\n@@ -1,2 +1,2 @@\n- x=1\n+ x = 1\n",
  "patched_code": "x = 1\nprint(\"Hello\")",
  "success": true,
  "error": null
}

🧪 Run Tests
pytest -q

📈 Future Enhancements

GitHub PR Bot (Automatic Reviews)

Web UI Dashboard

Multi-language Support

Code Complexity Metrics

Deployment on HuggingFace / Render

🧑‍💻 Author

Your Name
Computer Science Graduate | Python & ML Developer

📄 License

This project is licensed under the MIT License — see the LICENSE
 file.
