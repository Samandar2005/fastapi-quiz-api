from fastapi import APIRouter, Depends, HTTPException
from models import Question, Answer, User
from auth import get_current_user
from schemas import QuestionCreate, QuestionResponse, AnswerResponse
from typing import List

router = APIRouter()


@router.post("/questions/", response_model=QuestionResponse)
async def create_question(question: QuestionCreate, current_user: User = Depends(get_current_user)):
    new_question = await Question.create(**question.dict())
    await new_question.fetch_related("answers")
    return QuestionResponse(
        id=new_question.id,
        text=new_question.text,
        category=new_question.category,
        difficulty=new_question.difficulty,
        answers=[
            AnswerResponse(id=a.id, text=a.text, is_correct=a.is_correct, question_id=a.question_id)
            for a in new_question.answers
        ],
    )


@router.get("/questions/", response_model=List[QuestionResponse])
async def get_questions(skip: int = 0, limit: int = 10, current_user: User = Depends(get_current_user)):
    items = await Question.all().prefetch_related("answers").offset(skip).limit(limit)
    results: list[QuestionResponse] = []
    for q in items:
        results.append(
            QuestionResponse(
                id=q.id,
                text=q.text,
                category=q.category,
                difficulty=q.difficulty,
                answers=[
                    AnswerResponse(id=a.id, text=a.text, is_correct=a.is_correct, question_id=a.question_id)
                    for a in q.answers
                ],
            )
        )
    return results
