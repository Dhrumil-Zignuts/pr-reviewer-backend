# PR Reviewer API

A production-ready FastAPI backend with GitHub OAuth authentication, modular monolithic architecture, and clean separation of concerns.

## Tech Stack

- **FastAPI**: Modern, fast (high-performance), web framework for building APIs with Python 3.11+.
- **SQLAlchemy (Async)**: SQL toolkit and Object-Relational Mapper for Python.
- **Alembic**: Lightweight database migration tool.
- **PostgreSQL**: Open-source relational database.
- **Pydantic V2**: Data validation and settings management using Python type annotations.
- **GitHub OAuth**: Secure authentication flow.

## Project Structure

```text
app/
├── core/           # Config, Security, Dependencies
├── models/         # SQLAlchemy models
├── schemas/        # Pydantic models (Request/Response)
├── repositories/   # Database operations (Layer between Service and DB)
├── services/       # Business logic (Layer between Routes and Repositories)
├── routes/         # FastAPI endpoints
├── common/         # Constants, Utils
├── exceptions/     # Custom exceptions and handlers
├── responses/      # Standard API response formatters
├── middleware/     # Custom middlewares (Logging, CORS)
├── db/             # Database connection and session management
└── scripts/        # Utility scripts (init_db, migrations)
main.py             # Application entry point
```

## Setup Instructions

### 1. Prerequisites

- Python 3.11+
- PostgreSQL
- Redis (Optional)

### 2. Environment Variables

Copy `.env.example` to `.env` and fill in your details:

```bash
cp .env.example .env
```

Ensure you have created a GitHub OAuth App and obtained the `CLIENT_ID` and `CLIENT_SECRET`. Set the `REDIRECT_URI` to `http://localhost:8000/api/v1/auth/github/callback`.

### 3. Installation

```bash
pip install -r requirements.txt
```

### 4. Database Migrations

Initialize the database and run migrations:

```bash
# Run migration
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# OR run the init script (for quick dev setup)
python -m app.scripts.init_db
```

### 5. Running the Application

```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the application is running, you can access the interactive API docs at:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## GitHub OAuth Flow

1. Redirect user to `/api/v1/auth/github/login` to start the flow.
2. User authenticates on GitHub and is redirected back to `/api/v1/auth/github/callback`.
3. The server exchanges the code for a GitHub token, fetches the user profile, and generates a JWT.
4. Use the JWT in subsequent requests via the `Authorization: Bearer <token>` header.

## Example Requests

### Get Current User

```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/users/me' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_jwt_token>'
```
