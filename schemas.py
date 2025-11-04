from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class AnswerCreate(BaseModel):
    text: str
    is_correct: bool


class AnswerResponse(AnswerCreate):
    id: int
    question_id: int
    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class QuestionCreate(BaseModel):
    text: str
    category_id: Optional[int] = None
    difficulty: Optional[str] = None


class QuestionResponse(QuestionCreate):
    id: int
    answers: List[AnswerResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
