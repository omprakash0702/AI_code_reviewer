# PR Guardian AI

> AI-Powered Repository Code Review Assistant

---

## About

PR Guardian AI is a developer tool that reviews any public GitHub repository and gives you a full code quality report in minutes. You paste a GitHub URL, and the system clones the repo, runs static analysis on every file, sends each file to an AI model for a deeper review, and returns a structured dashboard showing security vulnerabilities, bugs, performance issues, code quality problems, and suggested fixes — all scored and ranked by severity.

The idea is simple: most developers don't have time to review every file in a codebase carefully. PR Guardian AI does that automatically. It combines the precision of traditional lint tools with the contextual understanding of large language models to catch issues that neither approach finds alone. The output isn't just a list of warnings — it includes an explanation of why each issue matters, what the impact is, and a concrete fix with a code diff you can apply directly.

It also integrates with GitHub Actions so every pull request in your own repository gets reviewed automatically, with a bot comment summarising findings and an optional auto-fix branch opened with AI-generated patches applied.

---

## What it can do

- **Analyse any public GitHub repo** — paste a URL, get a full report in 3–6 minutes
- **Security scanning** — detects hardcoded secrets, SQL injection risks, missing auth checks, unsafe deserialization, and more
- **Bug detection** — finds silent exceptions, wrong conditionals, null dereferences, and data corruption risks
- **Performance analysis** — catches O(n²) loops, blocking calls in async handlers, N+1 query patterns, unbounded memory growth
- **Code quality review** — identifies missing error handling, misleading names, untestable design, and structural problems
- **Health score** — gives the repo a score out of 100 using a weighted formula with per-category caps, so one noisy category can't drag the whole score to zero
- **AI insights** — generates 4 specific architectural observations about the repo (not generic advice — observations specific to that codebase)
- **Side-by-side patch viewer** — shows current code vs AI-suggested fix with line-level diff highlighting
- **PR recommendation** — gives an Approve or Request Changes verdict with a confidence percentage and bullet-point reasoning
- **GitHub Actions integration** — automatically reviews every PR in your repo, posts a structured comment, and opens a draft fix branch with patches applied
- **Uptime monitoring** — pings the API every 15 minutes and automatically opens a GitHub issue if it goes down

---

## Tech stack

| Layer | What's used | Why |
|---|---|---|
| **Frontend** | React 18 + Vite 5 | Fast dev server, modern component model |
| **Styling** | TailwindCSS 3 | Utility-first, consistent dark theme |
| **Animation** | Framer Motion 11 | Smooth tab transitions and card reveals |
| **Charts** | Recharts 2 | Bar chart (by severity) + donut chart (by category) |
| **HTTP client** | Axios | 6-minute timeout for long analysis requests |
| **Backend** | FastAPI + Uvicorn | Fast async Python API, automatic OpenAPI docs |
| **AI model** | OpenAI gpt-4o-mini | Configurable — swap any OpenAI-compatible endpoint |
| **HTTP (AI calls)** | httpx | Synchronous calls to OpenAI API |
| **Static analysis** | Flake8, Pylint, Bandit, Black | Python lint, logic, security, formatting |
| **JS analysis** | ESLint, Prettier | JavaScript/TypeScript quality checks |
| **Git cloning** | subprocess + git CLI | Shallow clone (`--depth=1`) for fast repo access |
| **Data validation** | Pydantic v2 | Request/response schema enforcement |
| **Logging** | Python logging module | Dual output: console (INFO) + file (DEBUG) |
| **CI/CD** | GitHub Actions | 6 workflows: CI, deploy, security, monitor, review, release |
| **Dependency updates** | Dependabot | Weekly patch/minor updates, major versions blocked |

---

## Architecture

The system has three layers: a React frontend, a FastAPI backend, and external tools (AI model + static analyzers).

```
Browser (React)
      │
      │  POST /analyze-repo
      ▼
FastAPI Backend (server/app.py)
      │
      ├── 1. Clone repo (git clone --depth=1)
      │         server/analyzers/repo_scanner.py
      │
      ├── 2. Repository intelligence (1 AI call)
      │         server/ai/repo_reviewer.py → OpenAI API
      │         Returns: repo type, architecture summary, frameworks, AI insights
      │
      ├── 3. Per-file loop (up to 25 files)
      │     ├── Static analysis (subprocess)
      │     │     server/analyzers/python_analyzer.py → flake8, pylint, bandit, black
      │     │     server/analyzers/js_analyzer.py     → eslint, prettier
      │     │
      │     └── AI review (1 AI call per file)
      │           server/ai/repo_reviewer.py → OpenAI API
      │           Returns: issues with severity/category/fix + unified diff patch
      │
      ├── 4. Health score (no AI — deterministic formula)
      │         server/app.py → _calculate_health_score()
      │
      └── 5. PR summary (1 AI call)
                server/ai/repo_reviewer.py → OpenAI API
                Returns: recommendation (approve/request_changes) + findings
      │
      ▼
JSON response → React Dashboard
      │
      ├── Overview tab    (health score gauge, severity charts, repo intelligence)
      ├── Security tab    (expandable issue cards)
      ├── Performance tab
      ├── Bugs tab
      ├── Code Quality tab
      ├── Patches tab     (side-by-side diff viewer + fix suggestions)
      └── AI Summary tab  (recommendation card with confidence + bullet reasons)
```

**Key design decisions:**

- Static analysis runs *before* AI — the AI sees lint/security output as context, making its review more accurate and reducing hallucinations
- Health score is deterministic — not AI-generated — so it's reproducible and not subject to model drift
- Per-category caps on the health score formula prevent one noisy category (e.g. 60 code style warnings) from destroying an otherwise healthy score
- Shallow clone (`--depth=1`) keeps repository cloning under 5 seconds even for large repos
- Temp directory is always deleted in a `finally` block regardless of success or failure
- The AI model, API URL, and API key are all environment variables — the entire AI backend is swappable

---

## Project structure

```
aicodereviewer/
├── server/
│   ├── app.py                  # API routes: /review  /analyze-repo  /review-file
│   ├── logger.py               # Logging config — console + file
│   ├── ai/
│   │   ├── model.py            # Single-file reviewer (used by GitHub Actions /review)
│   │   ├── repo_reviewer.py    # Full repo reviewer — intelligence, per-file, summary
│   │   └── validation.py       # AI output normaliser and sanitiser
│   ├── analyzers/
│   │   ├── repo_scanner.py     # Git clone + file discovery + priority scoring
│   │   ├── python_analyzer.py  # Flake8 + Pylint + Bandit + Black
│   │   └── js_analyzer.py      # ESLint + Prettier
│   ├── diff/
│   │   └── safe_apply.py       # Hunk-based unified diff application
│   └── schemas/
│       ├── review_request.py   # /review endpoint schema
│       └── repo_analysis.py    # /analyze-repo request + response models
│
├── frontend/
│   └── src/
│       ├── App.jsx             # State machine: hero → loading → dashboard
│       ├── lib/
│       │   ├── api.js          # Axios client — POST /analyze-repo
│       │   └── utils.js        # Helpers: score colours, diff parser, severity styles
│       └── components/
│           ├── Hero.jsx              # Landing page + URL input
│           ├── LoadingState.jsx      # Live elapsed-time progress tracker
│           ├── Dashboard.jsx         # 7-tab navigation shell
│           ├── StatsGrid.jsx         # Health score gauge + stat cards
│           ├── SeverityChart.jsx     # Bar + donut charts
│           ├── RepoOverview.jsx      # Repo intelligence + AI insights
│           ├── IssuesPanel.jsx       # Expandable issue cards per category
│           ├── PatchViewer.jsx       # Side-by-side diff + fix suggestions
│           ├── AISummary.jsx         # Recommendation + confidence + reasoning
│           └── AnalysisTimeline.jsx  # Completed pipeline steps checklist
│
├── tests/
│   ├── unit/                   # Runs in CI — no API key needed
│   └── integration/            # Requires a live API + valid AI_API_KEY
│
└── .github/
    └── workflows/
        ├── ci.yml              # Lint + tests + frontend build on every push/PR
        ├── ai-code-review.yml  # AI reviews every PR, posts comment, opens fix branch
        ├── deploy.yml          # Deploy to Render (backend) + GitHub Pages (frontend)
        ├── security.yml        # CodeQL + pip-audit + npm audit + secret scan
        ├── monitor.yml         # Health check every 15 min, auto issue on outage
        └── release.yml         # Changelog + GitHub Release on version tags
```

---

## Setup

```bash
# 1. Backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Create .env
# AI_API_KEY=sk-...
# AI_MODEL=gpt-4o-mini
# AI_API_URL=https://api.openai.com/v1/chat/completions

uvicorn server.app:app --reload --port 8000

# 2. Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## Health score formula

Starts at 100. Deducts points per issue found. Each category has a hard cap so one noisy category can't sink the whole score.

| Category | Critical | High | Medium | Low | Cap |
|---|---|---|---|---|---|
| Security | −20 | −10 | −4 | −1.5 | 40 |
| Bugs | −15 | −7 | −2.5 | −0.8 | 25 |
| Performance | −8 | −4 | −1.5 | −0.5 | 15 |
| Code Quality | −4 | −1 | −0.4 | −0.1 | 15 |

Example: a repo with 55 low-severity code quality issues loses only 5.5 points (capped at 15), not 55 × 0.1 = 5.5 — same in this case, but 200 issues would still only lose 15.

---

## Environment variables

```env
AI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini
AI_API_URL=https://api.openai.com/v1/chat/completions
```

---

## License

MIT
