from pydantic import BaseModel, ConfigDict, Field
from typing import List


class AnswerCreate(BaseModel):
    text: str
    is_correct: bool


class AnswerResponse(AnswerCreate):
    id: int
    question_id: int
    model_config = ConfigDict(from_attributes=True)


class QuestionCreate(BaseModel):
    text: str
    category: str = None
    difficulty: str = None


class QuestionResponse(QuestionCreate):
    id: int
    answers: List[AnswerResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
