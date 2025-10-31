from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=100, unique=True)
    email = fields.CharField(max_length=100, unique=True)
    hashed_password = fields.CharField(max_length=200)
    is_active = fields.BooleanField(default=True)


class Question(Model):
    id = fields.IntField(pk=True)
    text = fields.TextField()
    category = fields.CharField(max_length=50, null=True)
    difficulty = fields.CharField(max_length=20, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)


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


class QuizResult(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='quiz_results', on_delete=fields.CASCADE)
    total_questions = fields.IntField()
    correct_answers = fields.IntField()
    completed_at = fields.DatetimeField(auto_now_add=True)
