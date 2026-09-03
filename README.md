# RootLearn

RootLearn is an AI-powered knowledge debugger. Instead of only answering a learner's question, it maps the prerequisite concepts, diagnoses the first weak foundation, and guides the learner toward real understanding.

## Why RootLearn?

A learner may struggle with recursion even though the actual weakness is a missing understanding of base cases or the call stack. RootLearn makes that dependency visible and tests each prerequisite before deciding what the learner should study next.

For example:

```text
Learner: "I understand functions, but recursion still confuses me."

Target: Recursion
Variables → Functions → Function Calls → Call Stack ─┐
                                                     ├→ Recursion
Control Flow → Conditionals → Base Case ─────────────┘
```

The graph is not only a diagram. Its mastery percentages and learning states change as diagnostic answers are evaluated.

## How it works

1. The learner describes what is confusing.
2. RootLearn builds an interactive prerequisite knowledge map.
3. Short diagnostic questions update mastery and confidence in real time.
4. The earliest important knowledge gap is highlighted on the map.
5. Guided teaching and teach-back help the learner close the gap.
6. The Progress view records mastery changes across the session.

## Features

- Interactive prerequisite graph with live mastery states
- Adaptive diagnostic questions and answer evaluation
- Root-gap detection inside the knowledge map
- Guided teaching and teach-back verification
- Session progress and mastery history
- Retry handling and a local development fallback when the AI provider is unavailable

## Tech stack

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS, React Flow, TanStack Query
- **Backend:** FastAPI, SQLAlchemy, Pydantic, NetworkX
- **Database:** PostgreSQL
- **AI:** OpenAI-compatible structured generation with validated outputs

## Architecture

```text
Browser
  │
  ▼
Next.js frontend ── REST/SSE ──► FastAPI backend
                                      │
                          ┌───────────┴───────────┐
                          ▼                       ▼
                   Learning services        AI provider
                          │
                          ▼
                     PostgreSQL
```

The AI provider handles semantic tasks such as concept extraction, question generation, and answer evaluation. Deterministic backend services validate the graph, calculate mastery, choose diagnostic concepts, and identify the root gap. This separation keeps learning-state updates predictable and testable.

## Main views

- **Overview:** Starts a session from a natural-language description of the learner's confusion.
- **Knowledge Map:** Displays prerequisites, dependencies, mastery levels, and the detected root gap.
- **Diagnosis:** Presents adaptive questions and updates the graph after each answer.
- **Teach-Back:** Verifies understanding through the learner's own explanation.
- **Progress:** Summarizes assessed concepts, current mastery, and mastery history.

## Run locally

### Requirements

- Node.js 20+
- Python 3.11+
- Docker with Docker Compose

### 1. Start PostgreSQL

```bash
docker compose up -d postgres
```

### 2. Start the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Add your OpenAI-compatible API key to `backend/.env`. For local development, `AI_LOCAL_FALLBACK_ENABLED=true` keeps the main flow available if the provider reaches its usage limit.

Main backend settings:

```env
DATABASE_URL=postgresql+asyncpg://rootlearn:rootlearn@localhost:5432/rootlearn
AI_PROVIDER=openai
OPENAI_API_KEY=your_api_key
AI_LOCAL_FALLBACK_ENABLED=true
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### 3. Start the frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Core API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/sessions` | Create and analyze a learning session |
| `POST` | `/api/v1/sessions/{id}/retry-analysis` | Retry failed session analysis |
| `GET` | `/api/v1/sessions/{id}/graph` | Read the current knowledge map |
| `GET` | `/api/v1/sessions/{id}/diagnosis/current` | Get the next diagnostic question |
| `POST` | `/api/v1/sessions/{id}/diagnosis/answer` | Evaluate an answer and update mastery |
| `GET` | `/api/v1/sessions/{id}/root-gap` | Read the detected foundational gap |
| `POST` | `/api/v1/sessions/{id}/teachback` | Evaluate the learner's explanation |
| `GET` | `/api/v1/sessions/{id}/mastery-events` | Read mastery history for Progress |

Most session endpoints require a `user_id` query parameter or request-body field. Swagger UI contains the complete request and response schemas.

## Tests

```bash
# Backend
cd backend && ./venv/bin/pytest

# Frontend
cd frontend && npm run type-check && npm run test:run
```

## Common checks

```bash
# Confirm the API is running
curl http://localhost:8000/api/v1/health

# Confirm PostgreSQL is running
docker compose ps postgres
```

If a knowledge map cannot be generated because the AI provider is temporarily unavailable, keep `AI_LOCAL_FALLBACK_ENABLED=true` during local development and use **Try analysis again**. If the frontend cannot reach the API, confirm that `NEXT_PUBLIC_API_URL` in `frontend/.env.local` is set to `http://localhost:8000` and that the frontend origin is included in `ALLOWED_ORIGINS`.

## Project structure

```text
rootlearn/
├── backend/      # FastAPI API, learning services, AI providers, and tests
├── frontend/     # Next.js interface and component tests
├── deployment/   # Production deployment and monitoring configuration
└── docker-compose.yml
```

For a concise walkthrough, see [DEMO_SCRIPT.md](DEMO_SCRIPT.md).
