# PR Guardian AI

> AI-Powered Repository Code Review Assistant

---

## About

PR Guardian AI is a developer tool that reviews any public GitHub repository and gives you a full code quality report in minutes. You paste a GitHub URL, and the system clones the repo, runs static analysis on every file, sends each file to an AI model for a deeper review, and returns a structured dashboard showing security vulnerabilities, bugs, performance issues, code quality problems, and suggested fixes — all scored and ranked by severity.

The idea is simple: most developers don't have time to review every file in a codebase carefully. PR Guardian AI does that automatically. It combines the precision of traditional lint tools with the contextual understanding of large language models to catch issues that neither approach finds alone. The output isn't just a list of warnings — it includes an explanation of why each issue matters, what the impact is, and a concrete fix with a code diff you can apply directly.

It also integrates with GitHub Actions so every pull request in your own repository gets reviewed automatically, with a bot comment summarising findings and an optional auto-fix branch opened with AI-generated patches applied.

> **⚠️ CI/CD status: work in progress.** The `CI`, `ai-code-review`, and `deploy` workflows are currently failing on `main` after the recent async-architecture rewrite (new dependencies, new endpoints, new env vars they haven't caught up to yet). `security.yml` and the GitHub Pages deploy are passing. Don't treat the GitHub Actions integration described below as verified working until these are green again.

---

## What it can do

- **Analyse any public GitHub repo** — paste a URL, get a live-progress scan of the whole repo (up to 300 files), with an upfront time estimate
- **Any text-based file, not just a handful of languages** — code, config, docs, and Jupyter notebooks (`.ipynb` cells are extracted so output/metadata noise doesn't drown out the code); only real binaries/archives/lockfiles are excluded
- **Full file inventory** — every file in the repo categorized by extension, not just the ones eligible for AI review
- **Ask AI chat** — ask follow-up questions about the repo; it can fetch and read any source file on demand, not just ones already flagged as issues
- **Security scanning** — detects hardcoded secrets, SQL injection risks, missing auth checks, unsafe deserialization, and more
- **Bug detection** — finds silent exceptions, wrong conditionals, null dereferences, and data corruption risks
- **Performance analysis** — catches O(n²) loops, blocking calls in async handlers, N+1 query patterns, unbounded memory growth
- **Code quality review** — identifies missing error handling, misleading names, untestable design, and structural problems
- **Health score** — gives the repo a score out of 100 using a weighted formula with per-category caps, so one noisy category can't drag the whole score to zero
- **AI insights** — generates 4 specific architectural observations about the repo (not generic advice — observations specific to that codebase)
- **Side-by-side patch viewer** — shows current code vs AI-suggested fix with line-level diff highlighting
- **PR recommendation** — gives an Approve or Request Changes verdict with a confidence percentage and bullet-point reasoning
- **GitHub Actions integration** — automatically reviews every PR in your repo, posts a structured comment, and opens a draft fix branch with patches applied *(⚠️ work in progress — currently failing on `main`, see status note above)*
- **Uptime monitoring** — pings the API every 15 minutes and automatically opens a GitHub issue if it goes down

---

## Tech stack

| Layer | What's used | Why |
|---|---|---|
| **Frontend** | React 18 + Vite 5 | Fast dev server, modern component model |
| **Styling** | TailwindCSS 3 | Utility-first, consistent dark theme |
| **Animation** | Framer Motion 11 | Smooth tab transitions and card reveals |
| **Charts** | Recharts 2 | Bar chart (by severity) + donut chart (by category) |
| **HTTP client** | Axios | Short timeouts everywhere — /analyze-repo returns near-instantly since cloning runs in the background, not on the request path |
| **Backend** | FastAPI + Uvicorn | Fast async Python API, automatic OpenAPI docs |
| **Job state** | Redis (falls back to in-process fakeredis for local dev) | Analysis runs as a background job; `analysis_id` keys progress/results/chat history |
| **Rate limiting** | slowapi | 5 analysis starts/hour per IP — a full scan can trigger 100s of AI calls |
| **AI model** | OpenAI gpt-4o-mini | Configurable — swap any OpenAI-compatible endpoint |
| **HTTP (AI calls)** | httpx | Async + concurrent (6 files at a time) for full-repo scans |
| **Static analysis** | Flake8, Pylint, Bandit, Black | Python lint, logic, security, formatting |
| **JS analysis** | ESLint, Prettier | JavaScript/TypeScript quality checks |
| **Git cloning** | subprocess + git CLI | Shallow clone (`--depth=1`) for fast repo access |
| **Data validation** | Pydantic v2 | Request/response schema enforcement |
| **Logging** | Python logging module | Dual output: console (INFO) + file (DEBUG) |
| **CI/CD** | GitHub Actions | 6 workflows: CI, deploy, security, monitor, review, release |
| **Dependency updates** | Dependabot | Weekly patch/minor updates, major versions blocked |

---

## Architecture

The system has three layers: a React frontend, a FastAPI backend, and external tools (AI model + static analyzers). A full repo scan can mean hundreds of AI calls, so analysis runs as an async background job — the browser starts a job and polls for progress rather than waiting on one long HTTP request.

```
Browser (React)
      │
      │  POST /analyze-repo  (rate-limited: 5/hour/IP)
      ▼
FastAPI Backend (server/app.py)
      │
      ├── Creates a job in Redis (server/jobs.py), status "cloning"
      │         Returns { analysis_id } — nothing else, on purpose: cloning is
      │         network-bound (can take 1s or 30s+ depending on GitHub/network
      │         conditions) and must NEVER be on this response's critical path,
      │         or a slow clone trips the frontend's request timeout even
      │         though the backend is working fine.
      │
      └── Background task (server/app.py → _run_analysis_job) runs async:
            │
            ├── 0. Clone repo + walk EVERY file (git clone --depth=1)
            │         server/analyzers/repo_scanner.py
            │         → file_inventory: full extension breakdown, not just AI-reviewable files
            │         → selects up to 300 eligible files by priority score
            │         → job status becomes "running"; file_inventory now visible via polling
            │
            ├── 1. Repository intelligence (1 AI call, informed by the FULL
            │      file inventory — not just the handful of files sampled —
            │      so it reflects the whole project before per-file review starts)
            │         server/ai/repo_reviewer.py → OpenAI API
            │
            ├── 2. Per-file review — CONCURRENT, 10 files at a time
            │     ├── Static analysis (subprocess, off the event loop via
            │     │     asyncio.to_thread, each tool capped at 30s so one
            │     │     hung linter can never stall the whole job)
            │     │     server/analyzers/python_analyzer.py → flake8, pylint, bandit, black
            │     │     server/analyzers/js_analyzer.py     → eslint, prettier
            │     └── AI review (1 async AI call per file)
            │           server/ai/repo_reviewer.py → OpenAI API
            │           Redis progress + ETA updated after each file completes
            │
            ├── 3. Health score (no AI — deterministic formula)
            ├── 4. PR summary + critical cross-file analysis (2 AI calls)
            └── Result written to Redis, job marked "complete"; temp clone deleted

Browser polls  GET /analysis/{id}/status   → { status, file_inventory, progress, estimated_seconds_remaining }
Browser fetches GET /analysis/{id}         → full result once status is "complete"
Browser chats  POST /analysis/{id}/chat    → { message } → { answer }
      │
      ▼
React Dashboard
      ├── Overview tab           (health score gauge, severity charts, file inventory)
      ├── Security/Perf/Bugs/Code Quality tabs
      ├── Patches tab            (side-by-side diff viewer + fix suggestions)
      ├── Critical Analysis tab  (cross-file systemic risk patterns)
      ├── AI Summary tab
      └── Ask AI tab             (chat about the repo — see below)
```

**The chatbot (`server/ai/chat.py`)** answers questions about the repo without keeping the clone around after analysis finishes. Per question: one AI call decides which specific files (if any) it needs to read, those are fetched on demand from `raw.githubusercontent.com` using the exact ref that was analyzed, then a second AI call answers using that content plus the analysis summary. This lets it read any file in the repo — not just ones already flagged as an issue.

**Key design decisions:**

- Static analysis runs *before* AI — the AI sees lint/security output as context, making its review more accurate and reducing hallucinations
- Health score is deterministic — not AI-generated — so it's reproducible and not subject to model drift
- Per-category caps on the health score formula prevent one noisy category (e.g. 60 code style warnings) from destroying an otherwise healthy score
- Analysis is a background job, not a blocking request — hundreds of files reviewed sequentially would blow every timeout in the chain (browser, load balancer, Render); concurrency + polling keeps wall-clock time reasonable. Cloning is part of that background work too, not a precondition for the response.
- 10x concurrency + subprocess timeouts are tuned so a ~150-file "medium" repo finishes comfortably under 3 minutes, with an ETA shown upfront and updated live during the scan
- Temp directory is always deleted in a `finally` block regardless of success or failure
- The chatbot re-fetches file content from GitHub on demand instead of persisting the clone — GitHub is the storage layer, not us
- The AI model, API URL, and API key are all environment variables — the entire AI backend is swappable

---

## Project structure

```
aicodereviewer/
├── server/
│   ├── app.py                  # API routes: /review  /analyze-repo  /analysis/{id}/*  /review-file
│   ├── jobs.py                 # Redis-backed async job store (progress, results, chat history)
│   ├── logger.py               # Logging config — console + file
│   ├── ai/
│   │   ├── model.py            # Single-file reviewer (used by GitHub Actions /review)
│   │   ├── repo_reviewer.py    # Full repo reviewer — intelligence, per-file (sync + async), summary
│   │   ├── chat.py             # Chatbot — on-demand file retrieval + Q&A over a completed analysis
│   │   └── validation.py       # AI output normaliser and sanitiser
│   ├── analyzers/
│   │   ├── repo_scanner.py     # Git clone + full file inventory + priority scoring (up to 300 files)
│   │   ├── python_analyzer.py  # Flake8 + Pylint + Bandit + Black
│   │   └── js_analyzer.py      # ESLint + Prettier
│   ├── diff/
│   │   ├── safe_apply.py       # Hunk-based unified diff application
│   │   ├── validate_patch.py   # Rejects malformed/no-op patches before they reach the UI
│   │   └── classify.py         # Tags each patch as code / comment / documentation
│   └── schemas/
│       ├── review_request.py   # /review endpoint schema
│       └── repo_analysis.py    # /analyze-repo, /analysis/*, chat request + response models
│
├── frontend/
│   └── src/
│       ├── App.jsx             # State machine: hero → loading (polling) → dashboard
│       ├── lib/
│       │   ├── api.js          # Axios client — start/poll/fetch analysis, chat
│       │   └── utils.js        # Helpers: score colours, diff parser, severity styles
│       └── components/
│           ├── Hero.jsx              # Landing page + URL input
│           ├── LoadingState.jsx      # Real progress from polling — done/total files, current file
│           ├── Dashboard.jsx         # Tab navigation shell
│           ├── StatsGrid.jsx         # Health score gauge + stat cards
│           ├── SeverityChart.jsx     # Bar + donut charts
│           ├── RepoOverview.jsx      # Repo intelligence + AI insights
│           ├── FileInventory.jsx     # Full file-by-extension breakdown
│           ├── IssuesPanel.jsx       # Expandable issue cards per category
│           ├── PatchViewer.jsx       # Side-by-side diff + fix suggestions, grouped by category
│           ├── CriticalAnalysis.jsx  # Cross-file systemic risk patterns
│           ├── AISummary.jsx         # Recommendation + confidence + reasoning
│           ├── ChatPanel.jsx         # Ask AI — chat about the repo
│           └── AnalysisTimeline.jsx  # Completed pipeline steps checklist
│
├── tests/
│   ├── unit/                   # Runs in CI — no API key needed, no network calls
│   └── integration/            # Runs in CI — mocked AI/Redis, exercises real endpoints
│
└── .github/
    └── workflows/
        ├── ci.yml              # Lint + unit + integration tests + frontend build on every push/PR — ⚠️ failing, WIP
        ├── ai-code-review.yml  # AI reviews every PR, posts comment, opens fix branch — ⚠️ failing, WIP
        ├── deploy.yml          # Deploy to Render (backend) + GitHub Pages (frontend) — ⚠️ failing, WIP
        ├── security.yml        # CodeQL + pip-audit + npm audit + secret scan — passing
        ├── monitor.yml         # Health check every 15 min, auto issue on outage — passing
        └── release.yml         # Changelog + GitHub Release on version tags
```

---

## Setup

```bash
# 1. Redis (optional but recommended — see note below)
docker compose up -d redis

# 2. Backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Create .env
# AI_API_KEY=sk-...
# AI_MODEL=gpt-4o-mini
# AI_API_URL=https://api.openai.com/v1/chat/completions
# REDIS_URL=redis://localhost:6379/0   # matches docker-compose.yml above

uvicorn server.app:app --reload --port 8000

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

**Why bother with real Redis locally?** Without `REDIS_URL` set, job state falls back to an in-process `fakeredis` instance — fine for a quick manual test, but `uvicorn --reload` restarts the whole Python process on every code change, which wipes that in-memory state instantly. Mid-scan, that looks like the analysis silently vanished (a 404 on the next status poll) rather than erroring cleanly. Real Redis is a separate process, so job state survives backend restarts — worth the one `docker compose up -d redis` if you're doing more than a single one-off run.

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
REDIS_URL=redis://localhost:6379/0   # optional locally, required for production
                                      # (multi-instance deploys need shared job state)
```

---

## License

MIT
