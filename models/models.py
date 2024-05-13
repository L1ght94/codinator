from pydantic import BaseModel
from typing import Optional, List

class Snippet(BaseModel):
    id: Optional[int] = None
    language: str
    description: str
    code: Optional[str] = None
    feedback: Optional[str] = None
    previous_messages: Optional[List[dict]] = []
    test_cases: Optional[str] = None
    test_case_history: Optional[List[dict]] = []

class Feedback(BaseModel):
    message: str