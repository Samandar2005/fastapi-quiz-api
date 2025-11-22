from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime


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
    time_limit_seconds: Optional[int] = None
    answers: Optional[List[AnswerCreate]] = None  # Optional list of answers to create with question


class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    category_id: Optional[int] = None
    difficulty: Optional[str] = None
    time_limit_seconds: Optional[int] = None


class QuestionResponse(BaseModel):
    id: int
    text: str
    category_id: Optional[int] = None
    category: Optional[str] = None  # Category name for convenience
    difficulty: Optional[str] = None
    time_limit_seconds: Optional[int] = None
    answers: List[AnswerResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class AnswerUpdate(BaseModel):
    text: Optional[str] = None
    is_correct: Optional[bool] = None

class QuizAttemptCreate(BaseModel):
    category_id: Optional[int] = None
    total_time_limit: Optional[int] = None
    difficulty: Optional[str] = None
    num_questions: Optional[int] = None
    randomize: Optional[bool] = False

class QuizAttemptResponse(BaseModel):
    id: int
    category: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    time_spent: Optional[int] = None
    total_time_limit: Optional[int] = None
    difficulty: Optional[str] = None
    num_questions: Optional[int] = None
    randomize: bool = False
    selected_count: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

class QuizResultResponse(BaseModel):
    id: int
    total_questions: int
    correct_answers: int
    score: float
    time_spent: Optional[int] = None
    timed_out: bool = False
    completed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserStatisticsResponse(BaseModel):
    total_quizzes: int
    total_questions_answered: int
    correct_answers: int
    average_score: float
    total_time_spent: int
    last_quiz_date: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class LeaderboardEntry(BaseModel):
    username: str
    total_quizzes: int
    average_score: float
    total_questions_answered: int
    model_config = ConfigDict(from_attributes=True)


class CategoryStatistics(BaseModel):
    category_id: int
    category_name: str
    total_quizzes: int
    total_questions_answered: int
    correct_answers: int
    average_score: float
    best_score: float
    worst_score: float
    total_time_spent: int
    model_config = ConfigDict(from_attributes=True)


class DatePeriodStatistics(BaseModel):
    period: str  # week, month, year
    total_quizzes: int
    total_questions_answered: int
    correct_answers: int
    average_score: float
    total_time_spent: int
    quizzes_by_day: Optional[dict] = None  # {date: count}
    model_config = ConfigDict(from_attributes=True)


class QuestionResultDetail(BaseModel):
    question_id: int
    question_text: str
    user_answer_id: Optional[int] = None
    user_answer_text: Optional[str] = None
    correct_answer_ids: List[int] = Field(default_factory=list)
    correct_answer_texts: List[str] = Field(default_factory=list)
    is_correct: bool
    time_spent: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class AttemptDetailsResponse(BaseModel):
    attempt_id: int
    category_name: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_questions: int
    correct_answers: int
    score: float
    time_spent: Optional[int] = None
    timed_out: bool
    question_details: List[QuestionResultDetail] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
