import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

class AISuggester:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY")
        self.model_name = os.getenv("AI_MODEL", "gpt-4o-mini")
        self.api_url = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")

        print("DEBUG API_KEY:", self.api_key)
        print("DEBUG MODEL:", self.model_name)
        print("DEBUG URL:", self.api_url)

    def generate_review(self, filename, code, analysis):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        prompt = f"""
You are an expert code reviewer. Your output MUST be STRICT VALID JSON.

RESPONSE SHAPE (literal JSON):
{{
  "issues": [
    {{
      "type": "style" | "bug" | "refactor" | "security",
      "line": <integer_or_null>,
      "message": "<string>",
      "confidence": <float_between_0_and_1>
    }}
  ],
  "patch": "<unified_diff>"
}}

IMPORTANT — DIFF RULES (MUST FOLLOW):
1. The "patch" field MUST be a GNU unified diff.
2. The patch MUST start with the header lines:
   --- a/{filename}
   +++ b/{filename}
3. Every change hunk MUST include a hunk header line using @@, e.g.:
   @@ -1,2 +1,2 @@
4. Hunks MUST contain explicit removed lines starting with '-' and added lines starting with '+'.
   Example:
   - x=1
   + x = 1
5. The patch MUST NOT contain Python f-strings using braces {{}}, and MUST NOT include unescaped braces.
6. Do NOT return plain file content — always return a proper unified diff with at least one '-' and one '+' line per hunk.
7. "issues" MUST be an array of OBJECTS (not strings). Line MUST be an integer or null. Confidence MUST be float.

Example patch (literal example you MUST follow exactly):

--- a/{filename}
+++ b/{filename}
@@ -1,2 +1,2 @@
- x=1
+ x = 1
- print('Hi')
+ print("Hi")

NOW review the file:

Filename: {filename}

--- CODE START ---
{code}
--- CODE END ---

Static Analysis:
{analysis}
"""


        data = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }

        # OPENAI REQUEST
        response = httpx.post(self.api_url, headers=headers, json=data, timeout=30)

        # 🔥 THIS IS ABSOLUTELY REQUIRED 🔥
        print("DEBUG RESPONSE:", response.text)

        try:
            raw = response.json()["choices"][0]["message"]["content"]
            return json.loads(raw)
        except Exception as e:
            print("DEBUG PARSE ERROR:", e)
            return {"issues": [], "patch": ""}
