from pydantic import BaseModel

class ReviewRequest(BaseModel):
    filename: str
    code: str
    analysis: dict
