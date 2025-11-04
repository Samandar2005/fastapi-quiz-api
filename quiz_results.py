from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime, timezone
from models import User, QuizAttempt, QuizResult, UserStatistics, Question, UserAnswer, Category
from auth import get_current_user
from schemas import (
    QuizAttemptCreate, QuizAttemptResponse, QuizResultResponse,
    UserStatisticsResponse, LeaderboardEntry
)

router = APIRouter()

@router.post("/attempts/", response_model=QuizAttemptResponse)
async def start_quiz_attempt(
    attempt_data: QuizAttemptCreate,
    current_user: User = Depends(get_current_user)
):
    category = None
    if attempt_data.category_id:
        category = await Category.get_or_none(id=attempt_data.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    attempt = await QuizAttempt.create(
        user=current_user,
        category=category,
        total_time_limit=attempt_data.total_time_limit,
    )
    return QuizAttemptResponse(
        id=attempt.id,
        category=category.name if category else None,
        started_at=attempt.started_at,
        completed_at=None,
        time_spent=None,
        total_time_limit=attempt.total_time_limit,
    )

@router.post("/attempts/{attempt_id}/complete", response_model=QuizResultResponse)
async def complete_quiz_attempt(
    attempt_id: int,
    current_user: User = Depends(get_current_user)
):
    attempt = await QuizAttempt.get_or_none(id=attempt_id, user=current_user)
    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")
    
    if attempt.completed_at:
        raise HTTPException(status_code=400, detail="Quiz attempt already completed")
    
    # Calculate results
    await attempt.fetch_related('category')
    
    await attempt.fetch_related('category')
    
    questions = None
    if attempt.category:
        questions = await Question.filter(category_id=attempt.category.id)
    else:
        questions = await Question.all()
    
    user_answers = []
    for question in questions:
        answers = await UserAnswer.filter(
            user=current_user,
            question=question
        ).prefetch_related('answer')
        user_answers.extend(answers)
    
    total_questions = len(user_answers)
    correct_answers = sum(1 for ua in user_answers if ua.answer.is_correct)
    score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Update attempt
    now = datetime.now(timezone.utc)
    actual_time_spent = int((now - attempt.started_at.replace(tzinfo=timezone.utc)).total_seconds())

    # Determine timeout and cap time_spent if total_time_limit is set
    timed_out = False
    final_time_spent = actual_time_spent
    if attempt.total_time_limit is not None:
        if actual_time_spent >= attempt.total_time_limit:
            timed_out = True
            final_time_spent = attempt.total_time_limit

    await attempt.update_from_dict({
        "completed_at": now,
        "time_spent": final_time_spent
    }).save()

    # Create result
    result = await QuizResult.create(
        attempt=attempt,
        user=current_user,
        total_questions=total_questions,
        correct_answers=correct_answers,
        score=score,
        timed_out=timed_out,
    )
    
    # Update user statistics
    stats = await UserStatistics.get_or_none(user=current_user)
    if not stats:
        stats = await UserStatistics.create(user=current_user)
    
    await stats.update_from_dict({
        "total_quizzes": stats.total_quizzes + 1,
        "total_questions_answered": stats.total_questions_answered + total_questions,
        "correct_answers": stats.correct_answers + correct_answers,
        "average_score": (stats.average_score * stats.total_quizzes + score) / (stats.total_quizzes + 1),
        "total_time_spent": stats.total_time_spent + final_time_spent,
        "last_quiz_date": now
    }).save()

    # Build response
    return QuizResultResponse(
        id=result.id,
        total_questions=result.total_questions,
        correct_answers=result.correct_answers,
        score=result.score,
        time_spent=final_time_spent,
        timed_out=timed_out,
        completed_at=result.completed_at,
    )

@router.get("/statistics/me", response_model=UserStatisticsResponse)
async def get_my_statistics(current_user: User = Depends(get_current_user)):
    stats = await UserStatistics.get_or_none(user=current_user)
    if not stats:
        stats = await UserStatistics.create(user=current_user)
    return UserStatisticsResponse.model_validate(stats)

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(limit: int = 10):
    stats = await UserStatistics.all().prefetch_related('user').order_by('-average_score').limit(limit)
    return [
        LeaderboardEntry(
            username=stat.user.username,
            total_quizzes=stat.total_quizzes,
            average_score=stat.average_score,
            total_questions_answered=stat.total_questions_answered
        )
        for stat in stats
    ]