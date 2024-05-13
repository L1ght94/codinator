from pydantic import BaseModel
from typing import Optional, List

class Snippet(BaseModel):
    id: Optional[int] = None
    language: str
    description: str
    code: Optional[str] = None
    feedback: Optional[str] = None
    previous_messages: Optional[List[dict]] = []

class Feedback(BaseModel):
    message: str