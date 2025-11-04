from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=100, unique=True)
    email = fields.CharField(max_length=100, unique=True)
    hashed_password = fields.CharField(max_length=200)
    is_active = fields.BooleanField(default=True)


class Category(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

class Question(Model):
    id = fields.IntField(pk=True)
    text = fields.TextField()
    category = fields.ForeignKeyField('models.Category', related_name='questions', null=True, on_delete=fields.SET_NULL)
    difficulty = fields.CharField(max_length=20, null=True)
    time_limit_seconds = fields.IntField(null=True)  # per-question time limit in seconds
    created_at = fields.DatetimeField(auto_now_add=True)

    async def get_category_name(self) -> str:
        if self.category:
            await self.fetch_related('category')
            return self.category.name
        return None


class Answer(Model):
    id = fields.IntField(pk=True)
    question = fields.ForeignKeyField('models.Question', related_name='answers', on_delete=fields.CASCADE)
    text = fields.TextField()
    is_correct = fields.BooleanField(default=False)


class UserAnswer(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='user_answers', on_delete=fields.CASCADE)
    question = fields.ForeignKeyField('models.Question', related_name='user_answers', on_delete=fields.CASCADE)
    answer = fields.ForeignKeyField('models.Answer', related_name='user_answers', on_delete=fields.CASCADE)
    answered_at = fields.DatetimeField(auto_now_add=True)


class QuizAttempt(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='quiz_attempts', on_delete=fields.CASCADE)
    category = fields.ForeignKeyField('models.Category', related_name='quiz_attempts', null=True, on_delete=fields.SET_NULL)
    started_at = fields.DatetimeField(auto_now_add=True)
    completed_at = fields.DatetimeField(null=True)
    time_spent = fields.IntField(null=True)  # in seconds
    total_time_limit = fields.IntField(null=True)  # overall quiz time limit in seconds
    difficulty_filter = fields.CharField(max_length=20, null=True)
    num_questions = fields.IntField(null=True)
    randomize = fields.BooleanField(default=False)
    selected_question_ids = fields.TextField(null=True)  # comma-separated question ids

class QuizResult(Model):
    id = fields.IntField(pk=True)
    attempt = fields.ForeignKeyField('models.QuizAttempt', related_name='results', on_delete=fields.CASCADE)
    user = fields.ForeignKeyField('models.User', related_name='quiz_results', on_delete=fields.CASCADE)
    total_questions = fields.IntField()
    correct_answers = fields.IntField()
    score = fields.FloatField()  # percentage
    timed_out = fields.BooleanField(default=False)
    completed_at = fields.DatetimeField(auto_now_add=True)

class UserStatistics(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='statistics', on_delete=fields.CASCADE)
    total_quizzes = fields.IntField(default=0)
    total_questions_answered = fields.IntField(default=0)
    correct_answers = fields.IntField(default=0)
    average_score = fields.FloatField(default=0.0)
    total_time_spent = fields.IntField(default=0)  # in seconds
    last_quiz_date = fields.DatetimeField(null=True)
