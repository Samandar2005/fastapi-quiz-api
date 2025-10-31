from fastapi import APIRouter, Depends, HTTPException
from models import Question, Answer, User
from auth import get_current_user
from schemas import QuestionCreate, QuestionResponse
from typing import List

router = APIRouter()


@router.post("/questions/", response_model=QuestionResponse)
async def create_question(question: QuestionCreate, current_user: User = Depends(get_current_user)):
    new_question = await Question.create(**question.dict())
    return new_question


@router.get("/questions/", response_model=List[QuestionResponse])
async def get_questions(skip: int = 0, limit: int = 10, current_user: User = Depends(get_current_user)):
    return await Question.all().prefetch_related("answers").offset(skip).limit(limit)
