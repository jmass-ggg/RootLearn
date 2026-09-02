# RootLearn Backend API

AI-powered knowledge debugger backend built with FastAPI, SQLAlchemy, and PostgreSQL.

## Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Docker & Docker Compose (for local development)

## Setup

### 1. Install Dependencies

Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Or using Poetry:

```bash
poetry install
poetry shell
```

### 2. Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and set your configuration:

```env
DATABASE_URL=postgresql+asyncpg://rootlearn:rootlearn@localhost:5432/rootlearn
AI_PROVIDER=openai
OPENAI_API_KEY=your_key_here
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Start PostgreSQL Database

Using Docker Compose:

```bash
docker-compose up -d postgres
```

Or use your own PostgreSQL instance and create the database:

```sql
CREATE DATABASE rootlearn;
CREATE USER rootlearn WITH PASSWORD 'rootlearn';
GRANT ALL PRIVILEGES ON DATABASE rootlearn TO rootlearn;
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

### 5. Start the Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, access the interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Health Check Endpoints

- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/db` - Health check with database connectivity test

Example:

```bash
curl http://localhost:8000/api/v1/health
```

Response:

```json
{
  "status": "healthy",
  "timestamp": "2026-09-01T15:00:00.000000",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Demo Fixtures

Pre-built demo scenario for presentations and testing:

```bash
# Quick start (cross-platform)
python demo_quickstart.py

# Or manually:
python seed_demo.py
```

This creates a complete learning session for "I don't understand recursion" with:
- Pre-built prerequisite graph (7 concepts, 9 edges)
- Diagnostic questions and attempts
- Socratic tutoring dialogue
- Teach-back evaluation
- Mastery tracking events

**Demo credentials**:
- Email: `demo@rootlearn.example`
- Session includes realistic progression from initial confusion to understanding

See [`DEMO_FIXTURES.md`](./DEMO_FIXTURES.md) for complete documentation.

## Project Structure

```
backend/
├── alembic/              # Database migrations
│   ├── env.py           # Alembic environment config
│   └── versions/        # Migration files
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point
│   ├── config.py        # Application settings
│   ├── database.py      # Database session management
│   ├── logging_config.py # Structured logging with correlation IDs
│   ├── middleware.py    # Request correlation middleware
│   └── routes/          # API route handlers
│       └── health.py    # Health check endpoints
├── tests/               # Test files
├── seed_demo.py         # Demo data seeder
├── demo_quickstart.py   # Cross-platform demo setup
├── demo_quickstart.sh   # Shell-based demo setup
├── .env                 # Environment variables (not in git)
├── .env.example         # Example environment file
├── alembic.ini          # Alembic configuration
└── pyproject.toml       # Python dependencies (Poetry)
```

## Development

### Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=app tests/
```

### Code Quality

Format code with Black:

```bash
black app/ tests/
```

Lint with Ruff:

```bash
ruff check app/ tests/
```

### Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback one migration:

```bash
alembic downgrade -1
```

## Logging

The application uses structured JSON logging with correlation IDs:

- All requests receive a unique `request_id` (or use `X-Request-ID` header if provided)
- Request IDs are included in all log entries and API responses
- Log level is configurable via `LOG_LEVEL` environment variable

## Architecture

### AI Provider Abstraction

The system supports multiple AI providers through a unified interface:

- OpenAI (default)
- Anthropic Claude
- Google Gemini

Configure via `AI_PROVIDER` environment variable.

### Async SQLAlchemy

All database operations use async SQLAlchemy for optimal performance:

- Async engine and session management
- Connection pooling configured
- Automatic transaction management via middleware

### Structured Logging

Uses `structlog` for structured JSON logging:

- Correlation IDs for request tracing
- Automatic context propagation
- Configurable log levels
- Production-ready JSON output

## Configuration

All configuration is managed through environment variables and Pydantic Settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `AI_PROVIDER` | AI provider to use (openai/anthropic/gemini) | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | Optional |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional |
| `GOOGLE_API_KEY` | Google API key | Optional |
| `ENVIRONMENT` | Environment (development/staging/production) | `development` |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `API_V1_PREFIX` | API version prefix | `/api/v1` |
| `ALLOWED_ORIGINS` | CORS allowed origins (JSON array) | `["http://localhost:3000"]` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `true` |

## Troubleshooting

### Database Connection Issues

Check if PostgreSQL is running:

```bash
docker-compose ps
```

Test database connectivity:

```bash
curl http://localhost:8000/api/v1/health/db
```

### Port Already in Use

If port 8000 is in use, specify a different port:

```bash
uvicorn app.main:app --reload --port 8001
```

### Module Not Found Errors

Ensure virtual environment is activated and dependencies are installed:

```bash
source venv/bin/activate  # or poetry shell
pip install -r requirements.txt  # or poetry install
```
