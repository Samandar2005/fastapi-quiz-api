from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from models import User, QuizAttempt, QuizResult, UserStatistics, Question, UserAnswer, Category, Answer
from auth import get_current_user
from schemas import (
    QuizAttemptCreate, QuizAttemptResponse, QuizResultResponse,
    UserStatisticsResponse, LeaderboardEntry, CategoryStatistics,
    DatePeriodStatistics, AttemptDetailsResponse, QuestionResultDetail
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
    # Build base query for selecting questions according to settings
    qquery = Question.all()
    if category:
        qquery = qquery.filter(category_id=category.id)
    if attempt_data.difficulty:
        qquery = qquery.filter(difficulty=attempt_data.difficulty)

    # fetch matching questions
    matching_questions = await qquery.prefetch_related('answers')
    q_ids = [q.id for q in matching_questions]

    # apply randomization and limit
    selected_ids = q_ids
    if attempt_data.randomize and selected_ids:
        import random
        random.shuffle(selected_ids)
    if attempt_data.num_questions is not None and selected_ids:
        selected_ids = selected_ids[: attempt_data.num_questions]

    selected_csv = ",".join(str(i) for i in selected_ids) if selected_ids else None

    attempt = await QuizAttempt.create(
        user=current_user,
        category=category,
        total_time_limit=attempt_data.total_time_limit,
        difficulty_filter=attempt_data.difficulty,
        num_questions=attempt_data.num_questions,
        randomize=bool(attempt_data.randomize),
        selected_question_ids=selected_csv,
    )

    return QuizAttemptResponse(
        id=attempt.id,
        category=category.name if category else None,
        started_at=attempt.started_at,
        completed_at=None,
        time_spent=None,
        total_time_limit=attempt.total_time_limit,
        difficulty=attempt.difficulty_filter,
        num_questions=attempt.num_questions,
        randomize=attempt.randomize,
        selected_count=(len(selected_ids) if selected_ids else 0),
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
    
    # Determine selected questions for scoring
    selected_ids = None
    if attempt.selected_question_ids:
        try:
            selected_ids = [int(x) for x in attempt.selected_question_ids.split(",") if x]
        except Exception:
            selected_ids = None

    correct_answers = 0
    if selected_ids is not None:
        # total questions is the number of selected ids
        total_questions = len(selected_ids)
        # for each selected question, see if user provided a correct answer
        for qid in selected_ids:
            ua = await UserAnswer.filter(user=current_user, question_id=qid).prefetch_related('answer')
            # if any answer for that question and it's correct, count as correct
            for single in ua:
                if single.answer and single.answer.is_correct:
                    correct_answers += 1
                    break
    else:
        # fallback: use all questions in category (previous behavior)
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


@router.get("/statistics/me/by-category", response_model=List[CategoryStatistics])
async def get_statistics_by_category(current_user: User = Depends(get_current_user)):
    """Get statistics grouped by category for current user."""
    # Get all completed attempts for the user
    attempts = await QuizAttempt.filter(
        user=current_user,
        completed_at__isnull=False
    ).prefetch_related('category')
    
    # Get all results for these attempts
    results = await QuizResult.filter(
        user=current_user
    ).prefetch_related('attempt__category')
    
    # Group by category
    category_stats = {}
    
    for result in results:
        await result.fetch_related('attempt__category')
        category = result.attempt.category
        
        if category:
            cat_id = category.id
            cat_name = category.name
            
            if cat_id not in category_stats:
                category_stats[cat_id] = {
                    'category_id': cat_id,
                    'category_name': cat_name,
                    'total_quizzes': 0,
                    'total_questions_answered': 0,
                    'correct_answers': 0,
                    'scores': [],
                    'total_time_spent': 0
                }
            
            stats = category_stats[cat_id]
            stats['total_quizzes'] += 1
            stats['total_questions_answered'] += result.total_questions
            stats['correct_answers'] += result.correct_answers
            stats['scores'].append(result.score)
            # Get time_spent from attempt
            await result.fetch_related('attempt')
            stats['total_time_spent'] += (result.attempt.time_spent or 0)
    
    # Build response
    response = []
    for cat_id, stats in category_stats.items():
        scores = stats['scores']
        avg_score = sum(scores) / len(scores) if scores else 0.0
        best_score = max(scores) if scores else 0.0
        worst_score = min(scores) if scores else 0.0
        
        response.append(CategoryStatistics(
            category_id=stats['category_id'],
            category_name=stats['category_name'],
            total_quizzes=stats['total_quizzes'],
            total_questions_answered=stats['total_questions_answered'],
            correct_answers=stats['correct_answers'],
            average_score=avg_score,
            best_score=best_score,
            worst_score=worst_score,
            total_time_spent=stats['total_time_spent']
        ))
    
    return response


@router.get("/statistics/me/by-date", response_model=DatePeriodStatistics)
async def get_statistics_by_date(
    period: str = Query(..., description="Period: week, month, or year"),
    current_user: User = Depends(get_current_user)
):
    """Get statistics grouped by date period for current user."""
    now = datetime.now(timezone.utc)
    
    # Calculate start date based on period
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:
        raise HTTPException(status_code=400, detail="Period must be 'week', 'month', or 'year'")
    
    # Get results in the period
    results = await QuizResult.filter(
        user=current_user,
        completed_at__gte=start_date
    ).prefetch_related('attempt')
    
    # Calculate statistics
    total_quizzes = len(results)
    total_questions_answered = sum(r.total_questions for r in results)
    correct_answers = sum(r.correct_answers for r in results)
    # Get time_spent from attempt
    total_time_spent = 0
    for r in results:
        await r.fetch_related('attempt')
        total_time_spent += (r.attempt.time_spent or 0)
    scores = [r.score for r in results]
    average_score = sum(scores) / len(scores) if scores else 0.0
    
    # Group by day
    quizzes_by_day = {}
    for result in results:
        await result.fetch_related('attempt')
        date_key = result.completed_at.date().isoformat()
        quizzes_by_day[date_key] = quizzes_by_day.get(date_key, 0) + 1
    
    return DatePeriodStatistics(
        period=period,
        total_quizzes=total_quizzes,
        total_questions_answered=total_questions_answered,
        correct_answers=correct_answers,
        average_score=average_score,
        total_time_spent=total_time_spent,
        quizzes_by_day=quizzes_by_day
    )


@router.get("/attempts/{attempt_id}/details", response_model=AttemptDetailsResponse)
async def get_attempt_details(
    attempt_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get detailed results for a specific quiz attempt."""
    attempt = await QuizAttempt.get_or_none(id=attempt_id, user=current_user)
    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz attempt not found")
    
    await attempt.fetch_related('category')
    
    # Get result for this attempt
    result = await QuizResult.get_or_none(attempt=attempt, user=current_user)
    if not result:
        raise HTTPException(status_code=404, detail="Quiz result not found")
    
    # Get selected question IDs
    selected_ids = []
    if attempt.selected_question_ids:
        try:
            selected_ids = [int(x) for x in attempt.selected_question_ids.split(",") if x]
        except Exception:
            pass
    
    if not selected_ids:
        # Fallback: get all questions from category
        if attempt.category:
            questions = await Question.filter(category_id=attempt.category.id)
        else:
            questions = await Question.all()
        selected_ids = [q.id for q in questions]
    
    # Get question details
    question_details = []
    for qid in selected_ids:
        question = await Question.get_or_none(id=qid)
        if not question:
            continue
        
        # Get user's answer for this question
        user_answers = await UserAnswer.filter(
            user=current_user,
            question_id=qid
        ).prefetch_related('answer')
        
        # Get correct answers
        correct_answers = await Answer.filter(
            question_id=qid,
            is_correct=True
        )
        
        # Determine if user answered correctly
        is_correct = False
        user_answer_id = None
        user_answer_text = None
        
        for ua in user_answers:
            user_answer_id = ua.answer_id
            user_answer_text = ua.answer.text if ua.answer else None
            if ua.answer and ua.answer.is_correct:
                is_correct = True
                break
        
        correct_answer_ids = [a.id for a in correct_answers]
        correct_answer_texts = [a.text for a in correct_answers]
        
        question_details.append(QuestionResultDetail(
            question_id=question.id,
            question_text=question.text,
            user_answer_id=user_answer_id,
            user_answer_text=user_answer_text,
            correct_answer_ids=correct_answer_ids,
            correct_answer_texts=correct_answer_texts,
            is_correct=is_correct,
            time_spent=None  # Could be calculated if we track per-question time
        ))
    
    return AttemptDetailsResponse(
        attempt_id=attempt.id,
        category_name=attempt.category.name if attempt.category else None,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        total_questions=result.total_questions,
        correct_answers=result.correct_answers,
        score=result.score,
        time_spent=attempt.time_spent,
        timed_out=result.timed_out,
        question_details=question_details
    )