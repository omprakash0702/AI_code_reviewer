from pydantic import BaseModel
from typing import List, Optional

class Issue(BaseModel):
    type: str
    line: Optional[int]
    message: str
    confidence: float

class ReviewResponse(BaseModel):
    issues: List[Issue]
    patch: str
    patched_code: str
    success: bool
    error: Optional[str] = None
