import os

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # dotenv is optional in production; ignore if unavailable
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:1234@localhost:5432/quiz_db")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-.env")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
