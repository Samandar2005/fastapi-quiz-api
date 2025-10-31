from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from auth import router as auth_router
from quiz import router as quiz_router
from config import DATABASE_URL

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(quiz_router, prefix="/quiz", tags=["quiz"])

register_tortoise(
    app,
    db_url=DATABASE_URL,
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)
