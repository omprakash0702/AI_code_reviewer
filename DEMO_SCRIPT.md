# PR Guardian AI — 3-Minute Demo Script

---

## Hook (0:00–0:20)

> "Every developer has merged code they shouldn't have. A security bug, a null pointer crash, a slow query that kills the database. PR reviews catch some of it — but manual review is slow, inconsistent, and skips the boring files.
>
> This is PR Guardian AI: drop a GitHub URL, get a full AI-powered code audit in under a minute."

---

## Live Demo (0:20–2:10)

### Step 1 — Hero Page (0:20–0:35)

Open `http://localhost:5173`.

> "The landing page. One input: a GitHub URL. No setup, no config, no tokens needed."

Paste: `https://github.com/tiangolo/fastapi` (or any public repo)

Click **Analyze Repo**.

---

### Step 2 — Loading State (0:35–1:00)

> "The system clones the repository, identifies the most important files using a priority scoring algorithm — entry points, core modules, config files — skipping node_modules, build artifacts, and generated code.
>
> Then it runs static analysis: Flake8, Pylint, Bandit for Python; ESLint for JavaScript. That analysis feeds into an AI review prompt alongside the raw code."

Watch the step indicators advance.

---

### Step 3 — Overview Tab (1:00–1:30)

> "Results. Four summary cards up top: Health Score — calculated from the weighted severity of every issue found — files analyzed, critical issues, and security vulnerabilities."

Point to the **Health Score gauge** animating.

> "Below: severity distribution bar chart on the left — Critical, High, Medium, Low — and a category donut on the right."

Point to the **Repository Intelligence card**.

> "The AI identified this as a FastAPI backend, detected SQLAlchemy and Pydantic, and summarized the architecture in plain English."

---

### Step 4 — Security Tab (1:30–1:50)

Click **Security**.

> "Issues grouped by severity. Click to expand any finding."

Expand a critical issue.

> "Each issue has: what it is, why it matters, the potential impact, and a concrete suggested fix. No vague 'this could be a problem' — actionable output."

---

### Step 5 — Patch Viewer (1:50–2:05)

Click **Patches**.

> "For files with fixable issues, the AI generates a unified diff — the exact change needed. Side-by-side: current code on the left, suggested fix on the right. Red lines removed, green lines added."

---

### Step 6 — AI Summary (2:05–2:10)

Click **AI Summary**.

> "PR-style recommendation: Approve or Request Changes. Severity breakdown bars. One place to decide if this code is ready to merge."

---

## Close (2:10–3:00)

> "What we built on top of an existing FastAPI backend:
>
> — Repository cloning and intelligent file prioritization
> — Enhanced AI review returning categorized issues: security, performance, bugs, code quality
> — Health score algorithm weighted by severity and category
> — A full React dashboard: animated hero, live progress, seven-tab results view, side-by-side diff viewer
>
> The backend is stateless — it clones, analyzes, and discards. The frontend is a pure read view. No database, no auth, no infrastructure overhead.
>
> This is PR Guardian AI."

---

## Key Numbers to Quote

| Metric | Value |
|--------|-------|
| Static analyzers | 10+ (Flake8, Pylint, Bandit, Black, ESLint, Prettier) |
| Issue categories | 4 (Security, Performance, Bugs, Code Quality) |
| Severity levels | 4 (Critical → Low) |
| Max files analyzed | 25 (prioritized) |
| Avg. analysis time | 30–90 seconds |
| Lines of new code | ~1,200 (frontend) + ~250 (backend) |

---

## Fallback if Demo Breaks

If the live analysis is slow or fails:

1. Show the hero page and explain the flow verbally
2. Walk through the component structure in the IDE
3. Show the `/analyze-repo` API schema and explain the health score algorithm
4. Emphasize: the backend is fully functional via curl/Postman even without the UI
