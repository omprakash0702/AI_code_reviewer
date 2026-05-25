# PR Guardian AI

**AI-Powered Repository Code Review Assistant**

Drop a GitHub URL. Get a full security audit, bug report, performance analysis, AI insights, and auto-fix patches — all in one dashboard. Also integrates with GitHub Actions to review every pull request automatically.

---

## What it does

PR Guardian AI combines two review strategies into one pipeline:

1. **Static analysis** — Flake8, Pylint, Bandit, Black, ESLint run against every file
2. **AI review** — GPT-4o-mini reads each file with the static analysis context and produces categorised findings, severity ratings, suggested fixes, and unified diff patches

The result is a structured report: health score, per-category issue lists, AI insights about the repo's architecture, a PR recommendation (Approve / Request Changes), and a side-by-side patch viewer.

---

## Architecture

```
aicodereviewer/
├── server/                        # FastAPI backend
│   ├── app.py                     # Routes: /review  /analyze-repo  /review-file
│   ├── logger.py                  # Shared logging → console (INFO) + logs/pr_guardian.log (DEBUG)
│   ├── ai/
│   │   ├── model.py               # AISuggester — single-file review (used by /review)
│   │   ├── repo_reviewer.py       # RepoReviewer — repo intelligence + enhanced per-file review
│   │   └── validation.py          # AI output normaliser for /review endpoint
│   ├── analyzers/
│   │   ├── __init__.py            # analyze_file() dispatcher
│   │   ├── repo_scanner.py        # Git shallow-clone + file discovery + priority scoring
│   │   ├── common.py              # run_command() subprocess helper
│   │   ├── python_analyzer.py     # Flake8 + Pylint + Bandit + Black
│   │   └── js_analyzer.py         # ESLint + Prettier
│   ├── diff/
│   │   ├── patcher.py             # generate_diff / apply_patch (legacy)
│   │   └── safe_apply.py          # Hunk-based safe patch application
│   └── schemas/
│       ├── review_request.py      # ReviewRequest schema
│       ├── review_response.py     # ReviewResponse schema
│       └── repo_analysis.py       # RepoAnalysisRequest + full response models
│
├── frontend/                      # React + Vite + Tailwind dashboard
│   └── src/
│       ├── App.jsx                # Phase state machine: hero → loading → dashboard
│       ├── lib/
│       │   ├── api.js             # axios POST /analyze-repo (6-min timeout)
│       │   └── utils.js           # getScoreBg, parseDiff, getSeverityStyle helpers
│       └── components/
│           ├── Hero.jsx           # Landing page, URL input
│           ├── LoadingState.jsx   # Elapsed-time progress with real pipeline steps
│           ├── Dashboard.jsx      # Sticky header + 7-tab navigation
│           ├── StatsGrid.jsx      # Animated SVG health score gauge + stat cards
│           ├── SeverityChart.jsx  # Recharts bar + donut charts
│           ├── RepoOverview.jsx   # Repository intelligence + AI Insights
│           ├── IssuesPanel.jsx    # Expandable issue cards per category
│           ├── PatchViewer.jsx    # Side-by-side diff viewer + fix suggestions
│           ├── AISummary.jsx      # Recommendation card with confidence + bullet reasons
│           └── AnalysisTimeline.jsx  # Completed pipeline steps checklist
│
├── tests/
│   ├── unit/                      # pytest unit tests (no API key required)
│   └── integration/               # integration tests (require live API)
│
└── .github/
    ├── workflows/
    │   ├── ci.yml                 # Lint + unit tests + frontend build (Python matrix)
    │   ├── ai-code-review.yml     # AI reviews every PR, opens auto-fix branch
    │   ├── deploy.yml             # Deploy to Render + GitHub Pages on push to main
    │   ├── security.yml           # CodeQL + pip-audit + npm audit + secret scan
    │   ├── monitor.yml            # Health check every 15 min, auto issue on outage
    │   └── release.yml            # Auto-changelog + GitHub Release on version tags
    ├── dependabot.yml             # Weekly dependency updates (pip + npm + actions)
    └── pull_request_template.md   # PR checklist
```

---

## Stack

| Layer      | Technology                              |
|------------|-----------------------------------------|
| Frontend   | React 18 + Vite 5 + TailwindCSS 3      |
| Animation  | Framer Motion 11                        |
| Charts     | Recharts 2                              |
| Backend    | FastAPI + Uvicorn                       |
| AI         | OpenAI gpt-4o-mini (configurable)       |
| Analyzers  | Flake8, Pylint, Bandit, Black, ESLint   |
| Logging    | Python logging → file + console         |
| CI/CD      | GitHub Actions (6 workflows)            |

---

## Setup

### 1. Backend

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt

# Create .env in project root
# AI_API_KEY=sk-...
# AI_MODEL=gpt-4o-mini
# AI_API_URL=https://api.openai.com/v1/chat/completions

uvicorn server.app:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

The Vite dev server proxies `/analyze-repo` and `/review` to `http://localhost:8000`.

---

## API Reference

### `POST /analyze-repo` — full repository analysis

**Request:**
```json
{
  "repo_url": "https://github.com/username/repo",
  "branch": "main"
}
```

**Response:**
```json
{
  "health_score": 86,
  "files_analyzed": 20,
  "total_files_found": 31,
  "repository_intelligence": {
    "repo_type": "FastAPI REST API",
    "architecture_summary": "...",
    "important_modules": ["app.py", "model.py"],
    "detected_frameworks": ["FastAPI", "LangChain"],
    "primary_language": "Python",
    "ai_insights": [
      "Heavy LangChain dependency creates tight coupling",
      "..."
    ]
  },
  "issues": {
    "security": [...],
    "performance": [...],
    "bugs": [...],
    "code_quality": [...]
  },
  "severity_counts": { "critical": 0, "high": 1, "medium": 20, "low": 55 },
  "pr_summary": {
    "recommendation": "approve",
    "recommendation_reason": "...",
    "main_findings": "...",
    "files_analyzed": 20,
    "critical_risks": 0
  },
  "file_results": [
    { "filename": "server/app.py", "issues": [...], "patch": "unified diff or empty" }
  ]
}
```

### `POST /review` — single-file review (used by GitHub Actions)

```json
{ "filename": "app.py", "code": "...", "analysis": { "lint_issues": [] } }
```

### `GET /` — health check

Returns `{"status": "ok"}`.

---

## Analysis Pipeline

Each `/analyze-repo` request runs 5 sequential steps:

```
1. Clone repo (git clone --depth=1)
        ↓
2. Generate repository intelligence (1 AI call)
        ↓
3. For each file (up to 25):
   a. Static analysis  → Flake8, Bandit (subprocess)
   b. AI review        → categorised issues + patch (1 AI call per file)
        ↓
4. Calculate health score (deterministic formula, no AI)
        ↓
5. Generate PR summary (1 AI call)
```

Typical duration: **3–6 minutes** for a 20-file repo (sequential, one AI call per file).

---

## Health Score

Starts at 100 and deducts points per issue. Each category has a hard cap to prevent one noisy category from destroying the total score.

| Category     | Critical | High  | Medium | Low  | Cap |
|--------------|----------|-------|--------|------|-----|
| Security     | −20      | −10   | −4     | −1.5 | 40  |
| Bugs         | −15      | −7    | −2.5   | −0.8 | 25  |
| Performance  | −8       | −4    | −1.5   | −0.5 | 15  |
| Code Quality | −4       | −1    | −0.4   | −0.1 | 15  |

Minimum score: 0. Example: 55 low-severity code quality issues deducts only 5.5 pts (capped at 15).

---

## File Scanning

- **Supported:** `.py` `.js` `.ts` `.jsx` `.tsx` `.java` `.cpp` `.c`
- **Ignored:** `node_modules` `venv` `dist` `build` `.git` `__pycache__` `migrations` `static` `assets`
- **Max files:** 25 per analysis
- **Max file size:** 60 KB
- **Priority scoring:** entry points → config → auth/model → depth penalty

---

## Environment Variables

```env
AI_API_KEY=sk-...
AI_MODEL=gpt-4o-mini
AI_API_URL=https://api.openai.com/v1/chat/completions
```

---

## GitHub Actions CI/CD

| Workflow          | Trigger                      | What it does                                               |
|-------------------|------------------------------|------------------------------------------------------------|
| `ci.yml`          | Push / PR                    | Lint, unit tests (Python 3.10+3.11), frontend build        |
| `ai-code-review`  | PR opened / updated          | AI reviews changed files, posts comment, opens fix branch  |
| `deploy.yml`      | Push to main                 | Deploy backend (Render) + frontend (GitHub Pages)          |
| `security.yml`    | Push / PR / weekly Monday    | CodeQL, pip-audit, npm audit, secret scan                  |
| `monitor.yml`     | Every 15 minutes             | Health check, auto-creates/closes outage issue             |
| `release.yml`     | Tag `v*`                     | Auto-changelog + GitHub Release + frontend zip             |

### Required secrets

| Secret                   | Used by                | Description                          |
|--------------------------|------------------------|--------------------------------------|
| `REVIEW_API_URL`         | ai-code-review, monitor | Deployed API base URL                |
| `RENDER_DEPLOY_HOOK_URL` | deploy.yml             | From Render dashboard → Deploy Hook  |
| `API_URL`                | deploy.yml, monitor    | Same as REVIEW_API_URL               |

---

## Running Tests

```bash
# Unit tests only (no API key required)
pytest tests/unit -q

# With coverage
pytest tests/unit -q --cov=server --cov-report=term-missing

# Integration tests (requires running API + valid AI_API_KEY)
pytest tests/integration -q
```

---

## Logs

All pipeline steps write to `logs/pr_guardian.log` (DEBUG level) and stdout (INFO level).

```
2026-05-25 19:30:01.234  INFO     [app]           ANALYSIS START  https://github.com/...
2026-05-25 19:30:04.891  INFO     [repo_scanner]  Clone complete in 3.7s
2026-05-25 19:30:05.102  INFO     [app]           Step 3  [1/20]  server/app.py
2026-05-25 19:34:42.001  INFO     [app]           ANALYSIS COMPLETE  284.1s  score=86
```

---

## License

MIT
