## Quiz API (FastAPI + Tortoise ORM)

A minimal REST API for quizzes with JWT authentication. Built with FastAPI and Tortoise ORM. This project includes:

- Category management (create/list/update/delete)
- Question management with optional per-question time limits
- Quiz attempts with optional total quiz time limits
- Result tracking, user statistics and a leaderboard
- JWT authentication and pytest-based tests

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com/) [![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/) [![Tests](https://img.shields.io/badge/Tests-pytest-informational)](https://docs.pytest.org/)

### Quick links
- Run: `uvicorn main:app --reload`
- Docs: `http://127.0.0.1:8000/docs`

### Tech Stack
- **FastAPI** for the web framework
- **Tortoise ORM** (lightweight async ORM)
- **JWT** auth via `python-jose`
- **passlib[bcrypt]** for password hashing

### What this project provides

- User signup and token-based authentication (OAuth2 password flow)
- Category CRUD for organizing questions
- Question CRUD (create, read, update, delete) with optional per-question time limits
- Answer CRUD (create, read, update, delete) - manage answers independently
- Support for multiple correct answers per question
- Create questions with answers in a single request
- Start quiz attempts with an optional overall `total_time_limit` (seconds)
- Completing attempts computes score, records `time_spent`, and marks `timed_out` when limits are exceeded
- Per-user aggregated statistics and a global leaderboard
- Comprehensive tests that cover auth, questions, categories, answers, attempts and time-limit behavior

### Project structure (top-level files)
```text
auth.py        # Auth router + dependencies
quiz.py        # Quiz router: categories & questions
quiz_results.py # Quiz attempts, completion, statistics, leaderboard
models.py      # Tortoise models
schemas.py     # Pydantic request/response models
config.py      # Config (DATABASE_URL, JWT settings)
main.py        # App entry + Tortoise registration
tests/         # pytest tests
requirements.txt
```

### Configuration
Set configuration via environment variables or a `.env` file. Key vars used by the app:

- `DATABASE_URL` (example: `sqlite://:memory:` for tests or `postgres://user:pass@host:port/db`)
- `SECRET_KEY` (set a long random secret for production)
- `ALGORITHM` (e.g. `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (default: `30`)

Example `.env`:
```env
DATABASE_URL=postgres://postgres:password@localhost:5432/quiz_db
SECRET_KEY=your-very-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Database & migrations
During development the project uses Tortoise's `generate_schemas=True` to create tables automatically.
For production you should adopt a proper migration strategy.

### Models (high level)
- `User` — username, email, hashed_password, is_active
- `Category` — name, description
- `Question` — text, category (FK), difficulty, optional `time_limit_seconds`
- `Answer` — question (FK), text, is_correct
- `UserAnswer` — user, question, answer, answered_at
- `QuizAttempt` — user, category, started_at, completed_at, `time_spent`, optional `total_time_limit`
- `QuizResult` — attempt, user, total_questions, correct_answers, score, `timed_out`
- `UserStatistics` — aggregated per-user stats and averages

### Running locally

1. Create & activate virtualenv:

```powershell
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start the app:

```powershell
uvicorn main:app --reload
```

Interactive docs will be available at `http://127.0.0.1:8000/docs`.

### Authentication

Use the OAuth2 password flow to obtain a JWT:

- `POST /auth/signup` — register (JSON body: `username`, `email`, `password`)
- `POST /auth/token` — get token (form data: `username`, `password`)

The token response looks like:
```json
{"access_token": "<JWT>", "token_type": "bearer"}
```

Send the token in requests using the `Authorization: Bearer <JWT>` header.

### API Endpoints (high level)
Prefix: `/quiz`

Categories
- `POST /quiz/categories/` — Create a category
- `GET /quiz/categories/` — List all categories
- `GET /quiz/categories/{id}` — Get a category
- `PUT /quiz/categories/{id}` — Update
- `DELETE /quiz/categories/{id}` — Delete

Questions
- `POST /quiz/questions/` — Create a question
  - body example: `{ "text": "What is 2+2?", "category_id": 1, "difficulty": "easy", "time_limit_seconds": 10, "answers": [{"text": "4", "is_correct": true}, {"text": "5", "is_correct": false}] }`
  - Supports creating question with multiple answers (including multiple correct answers)
- `GET /quiz/questions/` — List questions; optional query `category_id`, `skip`, `limit`
- `GET /quiz/questions/{id}` — Get a single question with all its answers
- `PUT /quiz/questions/{id}` — Update a question (partial update supported)
- `DELETE /quiz/questions/{id}` — Delete a question

Answers
- `POST /quiz/questions/{question_id}/answers/` — Create an answer for a question
  - body example: `{ "text": "4", "is_correct": true }`
- `GET /quiz/questions/{question_id}/answers/` — Get all answers for a question
- `GET /quiz/answers/{id}` — Get a single answer
- `PUT /quiz/answers/{id}` — Update an answer (partial update supported)
- `DELETE /quiz/answers/{id}` — Delete an answer

Quiz attempts & results
- `POST /quiz/attempts/` — Start a quiz attempt (optional `{ "category_id": 1, "total_time_limit": 300 }`)
- `POST /quiz/attempts/{id}/complete` — Complete an attempt; server computes score, records `time_spent`, and sets `timed_out` when limits exceeded

Statistics & leaderboard
- `GET /quiz/statistics/me` — Get current user's aggregated statistics
- `GET /quiz/leaderboard` — Get top users ordered by average score (query param `limit` optional)

### Time limits behavior

- Per-question time limit: `Question.time_limit_seconds` is stored for a question and returned in the question response. Frontend should enforce per-question timers when presenting questions to users.
- Total quiz time limit: set via `QuizAttempt.total_time_limit` when starting an attempt. When completing an attempt the server calculates actual elapsed time and:
  - sets `timed_out` to `true` if elapsed time >= `total_time_limit` (inclusive),
  - caps `time_spent` to `total_time_limit` when the limit is exceeded.

Note: this implementation enforces total-time limits at attempt completion time (server-side). For stricter, real-time enforcement you can use client-side timers or websockets to auto-submit.

### Examples

Create question with per-question limit and multiple answers (including multiple correct answers):

```http
POST /quiz/questions/
Authorization: Bearer <JWT>
Content-Type: application/json

{
  "text": "Which numbers are even?",
  "category_id": 1,
  "difficulty": "easy",
  "time_limit_seconds": 15,
  "answers": [
    {"text": "2", "is_correct": true},
    {"text": "3", "is_correct": false},
    {"text": "4", "is_correct": true},
    {"text": "5", "is_correct": false}
  ]
}
```

Update a question:

```http
PUT /quiz/questions/{question_id}
Authorization: Bearer <JWT>
Content-Type: application/json

{
  "text": "Updated question text",
  "difficulty": "hard"
}
```

Create an answer for a question:

```http
POST /quiz/questions/{question_id}/answers/
Authorization: Bearer <JWT>
Content-Type: application/json

{
  "text": "New answer option",
  "is_correct": false
}
```

Update an answer:

```http
PUT /quiz/answers/{answer_id}
Authorization: Bearer <JWT>
Content-Type: application/json

{
  "text": "Updated answer text",
  "is_correct": true
}
```

Start an attempt with a 5-minute total limit:

```http
POST /quiz/attempts/
Authorization: Bearer <JWT>
Content-Type: application/json

{
  "category_id": 1,
  "total_time_limit": 300
}
```

Complete attempt:

```http
POST /quiz/attempts/{attempt_id}/complete
Authorization: Bearer <JWT>
```

Response includes `timed_out` and `time_spent` fields.

### Testing

Run tests locally (the project includes pytest tests that run against an in-memory or temporary DB configured in `tests/conftest.py`):

```powershell
pytest -q
```

All tests should pass; new tests include coverage for category CRUD, attempts/results, and time-limit enforcement.

### Troubleshooting

- If you see warnings about `python_multipart`, install `python-multipart` in your venv.
- For bcrypt/passlib issues, pin `bcrypt` if needed:

```powershell
pip install 'bcrypt~=4.1.3'
```

### Notes & next steps

- For production use, switch from auto-generating schemas to a proper migration workflow and ensure `SECRET_KEY` is secure.
- Consider adding realtime enforcement (websocket) if you need server-initiated auto-submit when time expires.

### License
MIT


