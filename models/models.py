from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class Snippet(BaseModel):
    id: Optional[int] = None
    language: str
    description: str
    code: Optional[str] = None
    feedback: Optional[str] = None
    previous_messages: Optional[List[Dict]] = Field(default_factory=list)
    tests: Optional[str] = None
    test_case_history: Optional[List[Dict]] = Field(default_factory=list)
    test_result: Optional[str] = None

class Feedback(BaseModel):
    message: str