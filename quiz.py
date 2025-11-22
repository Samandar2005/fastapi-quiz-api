from fastapi import APIRouter, Depends, HTTPException
from models import Question, Answer, User, Category
from auth import get_current_user
from schemas import (
    QuestionCreate, QuestionUpdate, QuestionResponse, AnswerResponse,
    AnswerCreate, AnswerUpdate, CategoryCreate, CategoryResponse
)
from typing import List, Optional

router = APIRouter()


@router.post("/categories/", response_model=CategoryResponse)
async def create_category(category: CategoryCreate, current_user: User = Depends(get_current_user)):
    new_category = await Category.create(**category.model_dump())
    return CategoryResponse.model_validate(new_category)

@router.get("/categories/", response_model=List[CategoryResponse])
async def get_categories(current_user: User = Depends(get_current_user)):
    categories = await Category.all()
    return [CategoryResponse.model_validate(cat) for cat in categories]

@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, current_user: User = Depends(get_current_user)):
    category = await Category.get_or_none(id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryResponse.model_validate(category)

@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user)
):
    category = await Category.get_or_none(id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    await category.update_from_dict(category_data.model_dump()).save()
    return CategoryResponse.model_validate(category)

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
    
    # Create question without answers first
    question_data = question.model_dump(exclude={'answers'})
    new_question = await Question.create(**question_data)
    
    # Create answers if provided
    if question.answers:
        for answer_data in question.answers:
            await Answer.create(question=new_question, **answer_data.model_dump())
    
    await new_question.fetch_related("answers", "category")
    return QuestionResponse(
        id=new_question.id,
        text=new_question.text,
        category_id=new_question.category_id,
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
                category_id=q.category_id,
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


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int, current_user: User = Depends(get_current_user)):
    question = await Question.get_or_none(id=question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    await question.fetch_related("answers", "category")
    
    return QuestionResponse(
        id=question.id,
        text=question.text,
        category_id=question.category_id,
        category=question.category.name if question.category else None,
        difficulty=question.difficulty,
        time_limit_seconds=question.time_limit_seconds,
        answers=[
            AnswerResponse(id=a.id, text=a.text, is_correct=a.is_correct, question_id=a.question_id)
            for a in question.answers
        ],
    )


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    question_data: QuestionUpdate,
    current_user: User = Depends(get_current_user)
):
    question = await Question.get_or_none(id=question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Validate category if provided
    if question_data.category_id is not None:
        category = await Category.get_or_none(id=question_data.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    # Update only provided fields
    update_dict = question_data.model_dump(exclude_unset=True)
    await question.update_from_dict(update_dict).save()
    
    await question.fetch_related("answers", "category")
    return QuestionResponse(
        id=question.id,
        text=question.text,
        category_id=question.category_id,
        category=question.category.name if question.category else None,
        difficulty=question.difficulty,
        time_limit_seconds=question.time_limit_seconds,
        answers=[
            AnswerResponse(id=a.id, text=a.text, is_correct=a.is_correct, question_id=a.question_id)
            for a in question.answers
        ],
    )


@router.delete("/questions/{question_id}")
async def delete_question(question_id: int, current_user: User = Depends(get_current_user)):
    question = await Question.get_or_none(id=question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    await question.delete()
    return {"message": "Question deleted successfully"}


# Answer endpoints
@router.post("/questions/{question_id}/answers/", response_model=AnswerResponse)
async def create_answer(
    question_id: int,
    answer: AnswerCreate,
    current_user: User = Depends(get_current_user)
):
    question = await Question.get_or_none(id=question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    new_answer = await Answer.create(question=question, **answer.model_dump())
    return AnswerResponse(
        id=new_answer.id,
        text=new_answer.text,
        is_correct=new_answer.is_correct,
        question_id=new_answer.question_id,
    )


@router.get("/questions/{question_id}/answers/", response_model=List[AnswerResponse])
async def get_question_answers(
    question_id: int,
    current_user: User = Depends(get_current_user)
):
    question = await Question.get_or_none(id=question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    answers = await Answer.filter(question_id=question_id)
    return [
        AnswerResponse(id=a.id, text=a.text, is_correct=a.is_correct, question_id=a.question_id)
        for a in answers
    ]


@router.get("/answers/{answer_id}", response_model=AnswerResponse)
async def get_answer(answer_id: int, current_user: User = Depends(get_current_user)):
    answer = await Answer.get_or_none(id=answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    return AnswerResponse(
        id=answer.id,
        text=answer.text,
        is_correct=answer.is_correct,
        question_id=answer.question_id,
    )


@router.put("/answers/{answer_id}", response_model=AnswerResponse)
async def update_answer(
    answer_id: int,
    answer_data: AnswerUpdate,
    current_user: User = Depends(get_current_user)
):
    answer = await Answer.get_or_none(id=answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    # Update only provided fields
    update_dict = answer_data.model_dump(exclude_unset=True)
    await answer.update_from_dict(update_dict).save()
    
    return AnswerResponse(
        id=answer.id,
        text=answer.text,
        is_correct=answer.is_correct,
        question_id=answer.question_id,
    )


@router.delete("/answers/{answer_id}")
async def delete_answer(answer_id: int, current_user: User = Depends(get_current_user)):
    answer = await Answer.get_or_none(id=answer_id)
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    await answer.delete()
    return {"message": "Answer deleted successfully"}
