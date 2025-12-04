⚙️ AI Code Reviewer — Configuration Guide

This document explains all environment variables, configuration files, and setup options used by the AI Code Reviewer project.

It is intended for:

Local development

Deployment (Render / HuggingFace)

CI/CD integration

OpenAI configuration

✅ 1. Environment Variables (.env File)

The project uses a .env file to securely store sensitive configuration.

📄 .env (Create in Project Root)
AI_API_KEY=your_openai_api_key_here
AI_MODEL=gpt-4o-mini
AI_API_URL=https://api.openai.com/v1/chat/completions

🔑 Variable Explanation
Variable	Purpose
AI_API_KEY	Your OpenAI secret API key
AI_MODEL	OpenAI model used for review
AI_API_URL	OpenAI Chat Completion API endpoint
⚠️ IMPORTANT SECURITY RULES

❌ Never commit .env to GitHub

✅ Ensure .env is listed in .gitignore

✅ Use GitHub Secrets for CI/CD

Your .gitignore must contain:

.env
venv/
__pycache__/

✅ 2. Local Development Configuration
Python Version
Python 3.10+

Virtual Environment
python -m venv venv
venv\Scripts\activate   # Windows

Dependency Installation
pip install -r requirements.txt

Run Server
uvicorn server.app:app --reload

✅ 3. OpenAI Configuration

The AI engine reads configuration from:

server/ai/model.py


It automatically loads:

load_dotenv()
os.getenv("AI_API_KEY")


No hardcoded API keys are used.

✅ 4. GitHub Actions Configuration (Future)

When you add CI/CD:

Setting	Location
OpenAI Key	GitHub → Repo → Settings → Secrets
Variable Name	AI_API_KEY

Used inside workflow like:

env:
  AI_API_KEY: ${{ secrets.AI_API_KEY }}

✅ 5. Deployment Configuration (Render / HuggingFace)

When deploying:

Platform	Where to Set Env
Render	Dashboard → Environment
HuggingFace	Space Settings → Secrets
GitHub CI	Secrets Section

Use the same keys as .env.

✅ 6. Testing Configuration

Tests do NOT call OpenAI directly.

Mocking is used in:

tests/unit/test_ai_wrapper.py


To run tests:

pytest -q

✅ 7. Port Configuration

Default local port:

8000


Swagger UI:

http://127.0.0.1:8000/docs

✅ 8. Optional Production Settings

For production use, recommended:

uvicorn server.app:app --host 0.0.0.0 --port 8000


Optional Gunicorn (Linux):

gunicorn -k uvicorn.workers.UvicornWorker server.app:app