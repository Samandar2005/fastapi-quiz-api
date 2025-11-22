import os

try:
    from dotenv import load_dotenv 
    load_dotenv()
except Exception:
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://db.sqlite3")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-.env")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
