from fastapi import APIRouter, Depends, HTTPException
from models import Question, Answer, User, Category
from auth import get_current_user
from schemas import (
    QuestionCreate, QuestionResponse, AnswerResponse,
    CategoryCreate, CategoryResponse
)
from typing import List, Optional

router = APIRouter()


@router.post("/categories/", response_model=CategoryResponse)
async def create_category(category: CategoryCreate, current_user: User = Depends(get_current_user)):
    new_category = await Category.create(**category.dict())
    return CategoryResponse.from_orm(new_category)

@router.get("/categories/", response_model=List[CategoryResponse])
async def get_categories(current_user: User = Depends(get_current_user)):
    categories = await Category.all()
    return [CategoryResponse.from_orm(cat) for cat in categories]

@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, current_user: User = Depends(get_current_user)):
    category = await Category.get_or_none(id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryResponse.from_orm(category)

@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user)
):
    category = await Category.get_or_none(id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    await category.update_from_dict(category_data.dict()).save()
    return CategoryResponse.from_orm(category)

@router.delete("/categories/{category_id}")
async def delete_category(category_id: int, current_user: User = Depends(get_current_user)):
    category = await Category.get_or_none(id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    await category.delete()
    return {"message": "Category deleted successfully"}

@router.post("/questions/", response_model=QuestionResponse)
async def create_question(question: QuestionCreate, current_user: User = Depends(get_current_user)):
    if question.category_id:
        category = await Category.get_or_none(id=question.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    new_question = await Question.create(**question.dict())
    await new_question.fetch_related("answers", "category")
    return QuestionResponse(
        id=new_question.id,
        text=new_question.text,
        category=new_question.category.name if new_question.category else None,
        difficulty=new_question.difficulty,
        time_limit_seconds=new_question.time_limit_seconds,
        answers=[
            AnswerResponse(id=a.id, text=a.text, is_correct=a.is_correct, question_id=a.question_id)
            for a in new_question.answers
        ],
    )


@router.get("/questions/", response_model=List[QuestionResponse])
async def get_questions(
    skip: int = 0,
    limit: int = 10,
    category_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    query = Question.all().prefetch_related("answers", "category")
    
    if category_id is not None:
        query = query.filter(category_id=category_id)
    
    items = await query.offset(skip).limit(limit)
    results: list[QuestionResponse] = []
    for q in items:
        results.append(
            QuestionResponse(
                id=q.id,
                text=q.text,
                category=q.category.name if q.category else None,
                difficulty=q.difficulty,
                time_limit_seconds=q.time_limit_seconds,
                answers=[
                    AnswerResponse(id=a.id, text=a.text, is_correct=a.is_correct, question_id=a.question_id)
                    for a in q.answers
                ],
            )
        )
    return results
