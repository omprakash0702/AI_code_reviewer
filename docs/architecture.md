🏗️ AI Code Reviewer — System Architecture

This document explains the overall architecture, data flow, and internal components of the AI Code Reviewer & Auto-Fix Tool.

It is written for:

Resume explanation

Interviews

System design understanding

Open-source contributors

✅ 1. High-Level Architecture Overview

The system follows a modular client–server architecture:

Client (UI / GitHub Action / Curl)
            |
            v
        FastAPI Server
            |
   +---------------------+
   | Static Analyzers    |
   | (Flake8, Pylint,    |
   | Bandit, ESLint)     |
   +---------------------+
            |
            v
        OpenAI API
            |
            v
     Unified Diff Patch
            |
            v
     Safe Patch Engine
            |
            v
       JSON API Response


✅ 2. Main Components
1️⃣ Client Layer

Can be:

Web UI

Curl / Postman

GitHub Actions

CI/CD pipelines

Sends:

Source code

File name

Static analysis result

Receives:

Issues

Patch

Auto-fixed code


2️⃣ API Layer (FastAPI)

Located in:

server/app.py


Responsibilities:

Input validation using Pydantic

REST endpoints

CORS handling

Error handling

Response formatting

Main Endpoints:

POST /review

POST /review-file

GET /

3️⃣ Static Analysis Engine

Located in:

server/analyzers/


Includes:

python_analyzer.py

js_analyzer.py

__init__.py

Tools used:

Flake8 → code style

Pylint → logic & quality

Bandit → security

ESLint → JavaScript linting

Function:

analyze_file(filepath)


Returns:

{
  "lint_issues": [],
  "security_issues": [],
  "format_suggestions": ""
}

4️⃣ AI Review Engine

Located in:

server/ai/model.py


Responsibilities:

Builds review prompt

Sends request to OpenAI

Enforces strict JSON output

Extracts issues and patch

Configuration from:

.env


Environment Variables:

AI_API_KEY
AI_MODEL
AI_API_URL

5️⃣ Validation Layer

Located in:

server/ai/validation.py


Responsibilities:

Ensures AI returns:

Valid JSON

Valid unified diff

Proper issue schema

Prevents malformed patches

6️⃣ Patch Engine (Safe Auto-Fix)

Located in:

server/diff/safe_apply.py


Responsibilities:

Validates unified diff format

Applies patch safely

Prevents file corruption

Returns:

Patched code

Success flag

Error message if needed

7️⃣ Schema Layer (Data Contracts)

Located in:

server/schemas/


Includes:

review_request.py

review_response.py

Uses Pydantic for:

Request validation

Response validation

Automatic OpenAPI docs

8️⃣ Testing Layer

Located in:

tests/
├── unit/
├── integration/


Test Scope:

AI wrapper

Analyzers

Patch engine

End-to-end API flow

Framework:

Pytest

✅ 3. Request Processing Flow (Step-by-Step)

Client sends request to:

POST /review


FastAPI validates request with Pydantic.

Static analysis results are passed to the AI engine.

AI engine:

Builds prompt

Calls OpenAI API

Receives review + unified diff patch

Validation layer verifies:

JSON correctness

Patch correctness

Patch engine applies the diff safely.

Final response is returned with:

Issues

Patch

Patched code

Success flag


✅ 4. Fault Tolerance & Error Handling

| Failure Point      | Handling                   |
| ------------------ | -------------------------- |
| Invalid JSON input | 422 Validation Error       |
| Invalid AI JSON    | Safe fallback response     |
| Invalid Patch      | Patch rejected             |
| Empty Patch        | Marked as failure          |
| OpenAI API Down    | Exception handled with 500 |

✅ 5. Security Design

API key stored in .env

.env excluded via .gitignore

Unified diff validation prevents:

Code injection

Arbitrary file overwrites

Static security scanner (Bandit) enabled

✅ 6. Scalability Design

The system is stateless and can scale via:

Container deployment (Docker)

Cloud deployment (Render / HuggingFace)

GitHub Action parallel runs

Horizontal FastAPI workers

✅ 7. Deployment Architecture
Developer → GitHub → CI → API Server → OpenAI
                               ↓
                          Response to Client


Supported:

Localhost

Render

HuggingFace Spaces

CI/CD pipelines

✅ 8. Why This Architecture is Resume-Ready

Modular design

Separation of concerns

Strong validation

Safe patching engine

AI integration

Industry-standard tooling

CI/CD ready