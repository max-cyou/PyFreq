
from pydantic import BaseModel, Field

class TextQuestion(BaseModel):
    question: str = Field(min_length=1)
    answers: list[str] = Field(min_length=2)

class TextResult(BaseModel):
    answer: str | None
    index: int | None
    confidence: float
