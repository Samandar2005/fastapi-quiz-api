## Quiz API (FastAPI + Tortoise ORM)

A minimal REST API for quizzes with JWT authentication. Built with FastAPI and Tortoise ORM, backed by PostgreSQL.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com/) [![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/) [![Tests](https://img.shields.io/badge/Tests-pytest-informational)](https://docs.pytest.org/)

### Quick links
- Run: `uvicorn main:app --reload`
- Docs: `http://127.0.0.1:8000/docs`
- Auth: `POST /auth/signup`, `POST /auth/token`, `GET /auth/me`
- Quiz: `POST /quiz/questions/`, `GET /quiz/questions/`

### Tech Stack
- **FastAPI** for the web framework
- **Tortoise ORM** with **PostgreSQL**
- **JWT** auth via `python-jose`
- **passlib[bcrypt]** for password hashing

### What does this project do?
- **Authenticates users via JWT** (`/auth/token`).
- Allows **creating questions** and **listing questions** (`/quiz/questions/`).
- Persists answers related to questions at the model level.
- All quiz endpoints are protected and require `Bearer <token>`.

### Key features
- **Quick start**: automatic schema generation (Tortoise `generate_schemas=True`).
- **Modular architecture**: separate auth and quiz routers.
- **Type safety**: request/response validation with Pydantic schemas.
- **Standard OAuth2 password flow** with `Authorization: Bearer <JWT>`.
 - **Tests included**: pytest-based suite (auth and quiz flows).

### Project Structure
```text
quiz_api/
  auth.py        # Auth router: token issuance + current user dependency
  quiz.py        # Quiz router: create/list questions (auth required)
  models.py      # Tortoise models: User, Question, Answer, UserAnswer, QuizResult
  schemas.py     # Pydantic schemas for request/response models
  config.py      # Configuration (DATABASE_URL, JWT config)
  main.py        # FastAPI app, router registration, Tortoise init
  requirements.txt
```

### How it works (short flow)
1) Client sends `username/password` to `POST /auth/token`.
2) Server validates the user and issues a **JWT**.
3) Client calls protected endpoints with `Authorization: Bearer <JWT>`.
4) Creating and fetching questions are handled by the quiz router.

### Requirements
See `requirements.txt`. Create and activate a virtualenv, then:

```bash
pip install -r requirements.txt
```

Optional (Windows):
```bash
python -m pip install --upgrade pip
```

### Configuration
Environment variables (via `.env` or system env):
- `DATABASE_URL` (default: `postgres://postgres:1234@localhost:5432/quiz_db`)
- `SECRET_KEY` (default: `change-me-in-.env`)
- `ALGORITHM` (default: `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (default: `30`)

Example `.env`:
```env
DATABASE_URL=postgres://postgres:password@localhost:5432/quiz_db
SECRET_KEY=your-very-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Database
Tortoise will auto-generate schemas on startup (`generate_schemas=True`). Ensure the target database exists and is reachable by `DATABASE_URL`.

Models (see `models.py`):
- `User(username, email, hashed_password, is_active)`
- `Question(text, category, difficulty, created_at)`
- `Answer(question -> Question, text, is_correct)`
- `UserAnswer(user, question, answer, answered_at)`
- `QuizResult(user, total_questions, correct_answers, completed_at)`

### Running
Development server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Interactive docs:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Authentication
OAuth2 Password flow with bearer tokens.

Token endpoint:
- `POST /auth/token` (form data: `username`, `password`)

The app exposes signup and token endpoints. Users are stored with bcrypt-hashed passwords.

Create the first user (development):
- Option A (generate a hash only):
  ```bash
  python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('secret'))"
  ```
  Then insert a user into the `User` table with the generated hash (via your DB client).

- Option B (small ORM script): initialize Tortoise and create a user using the `User` model.

Signup (cURL):
```bash
curl -X POST http://127.0.0.1:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"secret"}'
```

Token (cURL):
```bash
curl -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=secret" \
  http://127.0.0.1:8000/auth/token
```

Response:
```json
{"access_token":"<JWT>","token_type":"bearer"}
```

Use the token with `Authorization: Bearer <JWT>` for protected endpoints. To fetch the current user:

`GET /auth/me` (requires Authorization header)

### Quiz Endpoints
Prefix: `/quiz`

- `POST /quiz/questions/` — Create a question (auth required)
  - Body (JSON): `{ "text": "...", "category": "...", "difficulty": "..." }`
  - Response: `QuestionResponse` including generated `id`

- `GET /quiz/questions/?skip=0&limit=10` — List questions with their answers (auth required)
  - Query: `skip`, `limit`
  - Response: `List[QuestionResponse]`

Authorization header example:
```http
Authorization: Bearer <JWT>
```

Schemas (see `schemas.py`):
- `QuestionCreate`: `text`, optional `category`, `difficulty`
- `QuestionResponse`: `id`, fields from `QuestionCreate`, and `answers: List[AnswerResponse]`
- `AnswerResponse`: `id`, `text`, `is_correct`, `question_id`

### Quick Start (Local)
1) Prepare environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

2) Configure `.env` (see above) and ensure PostgreSQL is running and database exists.

3) Run server
```bash
uvicorn main:app --reload
```

4) Obtain token and call endpoints (via Swagger UI or cURL)

### API Overview
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/signup` | No | Create a new user |
| POST | `/auth/token` | No | Obtain JWT access token |
| GET | `/auth/me` | Yes | Get current authenticated user |
| POST | `/quiz/questions/` | Yes | Create a quiz question |
| GET | `/quiz/questions/` | Yes | List quiz questions |

### Testing
Run tests:
```bash
pytest -q
```
Notes:
- Tests use a temporary SQLite database by setting `DATABASE_URL` at runtime.
- Ensure virtualenv is active and dependencies are installed.

### Troubleshooting
- bcrypt warnings or 72-byte password error: we configure Passlib to avoid truncate errors; if issues persist, pin bcrypt:
  ```
  pip install 'bcrypt~=4.1.3'
  ```
- `python_multipart` warning: it’s a deprecation notice; already covered via `python-multipart` in requirements.
- Import issues during tests: ensure project root is on `sys.path` (handled in `tests/conftest.py`).

### Notes
- On first run, Tortoise will create tables automatically.
- For production, set a strong `SECRET_KEY` and consider migrations instead of auto-generate.
 - A public registration endpoint is available at `POST /auth/signup`.

### License
MIT (or your preferred license)


