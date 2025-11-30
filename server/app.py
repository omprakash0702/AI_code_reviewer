import json
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from server.schemas.review_request import ReviewRequest
from server.schemas.review_response import ReviewResponse
from server.ai.model import AISuggester
from server.ai.validation import validate_ai_output
from server.diff.safe_apply import safe_apply_patch
from server.analyzers import analyze_file


# -------------------------------------------------------------------
# App Initialization
# -------------------------------------------------------------------
app = FastAPI(title="AI Code Reviewer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# AI Model Initialization
# -------------------------------------------------------------------
ai = AISuggester()


# -------------------------------------------------------------------
# /review → Main API endpoint (used by GitHub Actions)
# -------------------------------------------------------------------
@app.post("/review", response_model=ReviewResponse)
def review_code(req: ReviewRequest):

    ai_result = ai.generate_review(req.filename, req.code, req.analysis)

    # Ensure raw output is dict
    if isinstance(ai_result, str):
        try:
            ai_result = json.loads(ai_result)
        except:
            return {
                "issues": [],
                "patch": "",
                "patched_code": req.code,
                "success": False,
                "error": "AI returned invalid JSON"
            }

    # 🔥 VALIDATE ISSUES AND PATCH
    validated = validate_ai_output(ai_result)

    # Apply patch safely
    applied = safe_apply_patch(req.code, validated["patch"])

    return {
        "issues": validated["issues"],
        "patch": validated["patch"],
        "patched_code": applied["patched_code"],
        "success": applied["success"],
        "error": applied["error"]
    }


# -------------------------------------------------------------------
# Health check
# -------------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "AI Code Reviewer API is running"}


# -------------------------------------------------------------------
# /review-file → Local testing only
# -------------------------------------------------------------------
@app.post("/review-file")
def review_file(payload: dict):

    filepath = payload.get("filepath")
    if not filepath:
        raise HTTPException(status_code=400, detail="filepath missing")

    try:
        analysis = analyze_file(filepath)

        with open(filepath, "r") as f:
            code = f.read()

        ai_result = ai.generate_review(filepath, code, analysis)
        validated = validate_ai_output(ai_result)
        patched = safe_apply_patch(code, validated["patch"])

        return {
            "analysis": analysis,
            "issues": validated["issues"],
            "patch": validated["patch"],
            "patched_code": patched["patched_code"],
            "success": patched["success"],
            "error": patched.get("error")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
