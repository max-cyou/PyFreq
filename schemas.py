
from pydantic import BaseModel, Field
from typing import Literal

class TextQuestion(BaseModel):
    question: str = Field(min_length=1)
    answers: list[str] = Field(min_length=2)
    timeout: int = Field(default=20, gt=0, description='Таймаут запроса к поисковику в секундах')
    backend: Literal[
        'auto', 'brave', 'duckduckgo', 'grokipedia',
        'mojeek', 'startpage', 'wikipedia', 'yahoo',
    ] = 'auto'
    max_results: int = Field(default=1, ge=1, description='Максимальное число вариантов ответа в candidates')
    confidence_gap: float = Field(default=0.1, ge=0, le=1, description='Максимальная разница confidence с лидером')

class TextCandidate(BaseModel):
    answer: str
    index: int
    confidence: float

class TextResult(BaseModel):
    answer: str | None
    index: int | None
    confidence: float
    candidates: list[TextCandidate] = Field(default_factory=list)
