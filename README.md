# RootLearn Knowledge Debugger

An AI-powered knowledge debugger that identifies root prerequisite gaps in a learner's understanding, teaches missing concepts through adaptive Socratic guidance, and verifies understanding with teach-back evaluation.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Features](#features)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Documentation](#documentation)

## Overview

RootLearn differs from traditional AI tutors by diagnosing **why** a learner cannot understand a concept and addressing the foundational knowledge gap.

### The Problem

Most AI tutors answer the question a learner asks. RootLearn asks: **"Why is this learner unable to understand this concept yet?"**

**Example:**

```
Student: "I don't understand React useEffect."

RootLearn identifies the prerequisite chain:
useEffect
  ↑
Side Effects
  ↑
Rendering   ← weak prerequisite detected (34% mastery)
  ↑
State       ← understood (84% mastery)
  ↑
Components  ← mastered (92% mastery)

Root gap: React Rendering
```

The system then teaches **React Rendering** before returning to `useEffect`.

### The Learning Loop

```
Student confusion
    ↓
1. Target concept detection
    ↓
2. Prerequisite graph generation
    ↓
3. Adaptive diagnosis (max 6 questions)
    ↓
4. Root knowledge-gap detection
    ↓
5. Socratic tutoring (progressive hints)
    ↓
6. Teach-back verification
    ↓
7. Deterministic mastery update
    ↓
8. Next learning step
```

### Design Principles

**Separation of Concerns:**
- **AI for semantic tasks**: Concept identification, question generation, answer evaluation, tutoring dialogue
- **Deterministic logic for learning state**: Mastery calculation, root-gap detection, learning path progression
- **This ensures**: Explainability, testability, reproducibility, and resistance to model inconsistency

**Core Values:**
- **Diagnostic-first**: Focus on identifying gaps, not just answering questions
- **Prerequisite-aware**: Build understanding from the foundation up
- **Evidence-based**: Transparent scoring based on multiple evidence types
- **Explainable**: Every decision has a clear reason
- **Testable**: Property-based testing ensures correctness

## Architecture

### High-Level System Design

```
┌─────────────┐
│   Learner   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Next.js/React Frontend             │
│  - Knowledge Graph Visualization    │
│  - Diagnostic Interface             │
│  - Socratic Tutor UI                │
│  - Teach-Back Interface             │
└──────────────┬──────────────────────┘
               │ REST JSON / SSE
               ▼
┌─────────────────────────────────────┐
│  FastAPI Backend                    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Service Layer              │   │
│  │  - Session Management       │   │
│  │  - Graph Service            │   │
│  │  - Diagnostic Service       │   │
│  │  - Mastery Engine           │   │
│  │  - Root Gap Service         │   │
│  │  - Tutor Service            │   │
│  │  - Teach-Back Service       │   │
│  │  - Learning Path Service    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  AI Provider Adapter        │   │
│  │  - OpenAI                   │   │
│  │  - Anthropic                │   │
│  │  - Google Gemini            │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Graph Validation           │   │
│  │  - NetworkX for DAG checks  │   │
│  └─────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  PostgreSQL Database                │
│  - Users, Sessions, Concepts        │
│  - Edges, Questions, Attempts       │
│  - Mastery Events, AI Runs          │
└─────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- Python 3.11+ with FastAPI
- SQLAlchemy 2 (async) with PostgreSQL
- Alembic for migrations
- NetworkX for graph algorithms
- Hypothesis for property-based testing
- Pydantic v2 for validation
- Structured logging with correlation IDs

**Frontend:**
- Next.js 15+ with React 18
- TypeScript (strict mode)
- Tailwind CSS
- React Flow for knowledge graph visualization
- TanStack Query for state management
- Zod for runtime validation

**Database:**
- PostgreSQL 16+

**Infrastructure:**
- Docker & Docker Compose for development
- Nginx for reverse proxy (production)
- Prometheus + Grafana for monitoring (optional)
- AlertManager for alerts (optional)

**AI Providers:**
- OpenAI (GPT-4, GPT-4 Turbo)
- Anthropic (Claude 3.5 Sonnet)
- Google (Gemini Pro)

### Key Components

**Core Services:**
- **SessionService**: Manages learning session lifecycle
- **GraphService**: Generates and validates prerequisite graphs using NetworkX
- **DiagnosticService**: Adaptive questioning engine with priority-based concept selection
- **MasteryService**: Deterministic mastery calculation (45% diagnostic, 35% practice, 20% teach-back)
- **RootGapService**: Identifies high-impact knowledge gaps using gap scoring formula
- **TutorService**: Socratic tutoring with progressive hint escalation
- **TeachBackService**: Validates understanding through learner explanations
- **LearningPathService**: Topological ordering for optimal learning sequence

**Data Models:**
- Users, LearningSession, Concept, ConceptEdge
- DiagnosticQuestion, DiagnosticAttempt
- TutorMessage, TeachBackAttempt
- MasteryEvent, AIRun

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+ (or Docker)
- Docker & Docker Compose (optional, for database)
- AI Provider API key (OpenAI, Anthropic, or Google)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rootlearn
```

### 2. Start the Database

**Option A: Using Docker Compose (Recommended)**

```bash
docker-compose up -d postgres
```

**Option B: Using Your Own PostgreSQL**

```sql
CREATE DATABASE rootlearn;
CREATE USER rootlearn WITH PASSWORD 'rootlearn';
GRANT ALL PRIVILEGES ON DATABASE rootlearn TO rootlearn;
```

### 3. Set Up Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set your configuration

# Example .env:
# DATABASE_URL=postgresql+asyncpg://rootlearn:rootlearn@localhost:5432/rootlearn
# AI_PROVIDER=openai
# OPENAI_API_KEY=sk-your-key-here

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`

### 4. Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Verify NEXT_PUBLIC_API_URL points to backend (default: http://localhost:8000)

# Start the development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

### 5. Verify Installation

```bash
# Check backend health
curl http://localhost:8000/api/v1/health

# Check database connectivity
curl http://localhost:8000/api/v1/health/db

# Access API documentation
open http://localhost:8000/docs
```

### Demo Data (Optional)

Load pre-built demo scenario for testing:

```bash
cd backend
python demo_quickstart.py
```

This creates a complete learning session for "I don't understand recursion" with diagnostic questions, tutoring dialogue, and mastery tracking.

## Project Structure

```
rootlearn/
├── README.md                     # This file
├── docker-compose.yml            # Docker development setup
├── docker-compose.prod.yml       # Production Docker setup
├── .env.production.example       # Production environment template
│
├── .kiro/specs/                  # Feature specifications
│   └── rootlearn-knowledge-debugger/
│       ├── requirements.md       # Formal EARS requirements
│       ├── design.md            # System design document
│       └── tasks.md             # Implementation plan
│
├── backend/                      # FastAPI backend
│   ├── alembic/                 # Database migrations
│   │   ├── env.py
│   │   └── versions/            # Migration files
│   ├── app/
│   │   ├── main.py              # Application entry point
│   │   ├── config.py            # Settings and configuration
│   │   ├── database.py          # Database session management
│   │   ├── logging_config.py   # Structured logging
│   │   ├── middleware.py        # Request correlation middleware
│   │   ├── error_handlers.py   # Global error handling
│   │   ├── models.py            # SQLAlchemy models
│   │   │
│   │   ├── ai/                  # AI provider abstraction
│   │   │   ├── factory.py       # Provider selection
│   │   │   ├── protocol.py      # AI provider interface
│   │   │   ├── schemas.py       # Pydantic schemas
│   │   │   ├── prompts.py       # Versioned prompts
│   │   │   └── providers/       # Provider implementations
│   │   │
│   │   ├── routes/              # API endpoints
│   │   │   ├── sessions.py
│   │   │   ├── graph.py
│   │   │   ├── diagnosis.py
│   │   │   ├── root_gap.py
│   │   │   ├── tutor.py
│   │   │   ├── teachback.py
│   │   │   └── health.py
│   │   │
│   │   └── services/            # Business logic
│   │       ├── session_service.py
│   │       ├── graph_service.py
│   │       ├── diagnostic_service.py
│   │       ├── mastery_service.py
│   │       ├── root_gap_service.py
│   │       ├── tutor_service.py
│   │       ├── teachback_service.py
│   │       └── learning_path_service.py
│   │
│   ├── tests/                   # Test suite
│   │   ├── unit/                # Unit tests
│   │   ├── property/            # Property-based tests (Hypothesis)
│   │   └── integration/         # Integration tests
│   │
│   ├── .env.example             # Environment template
│   ├── requirements.txt         # Python dependencies
│   ├── pyproject.toml           # Project metadata
│   ├── alembic.ini              # Alembic configuration
│   └── README.md                # Backend documentation
│
├── frontend/                    # Next.js frontend
│   ├── src/
│   │   ├── app/                 # Next.js App Router
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── page.tsx         # Landing page
│   │   │   ├── providers.tsx   # React Query provider
│   │   │   └── session/         # Session pages
│   │   │
│   │   ├── components/          # React components
│   │   │   ├── KnowledgeGraph.tsx
│   │   │   ├── DiagnosticPanel.tsx
│   │   │   ├── RootGapCard.tsx
│   │   │   ├── TutorPanel.tsx
│   │   │   ├── TeachBackPanel.tsx
│   │   │   └── MasteryBar.tsx
│   │   │
│   │   ├── lib/                 # Shared utilities
│   │   │   └── api.ts           # API client
│   │   │
│   │   └── types/               # TypeScript types
│   │
│   ├── public/                  # Static assets
│   ├── .env.local.example       # Environment template
│   ├── package.json             # Node dependencies
│   ├── tsconfig.json            # TypeScript config
│   ├── tailwind.config.ts       # Tailwind config
│   └── README.md                # Frontend documentation
│
└── deployment/                  # Production deployment
    ├── DEPLOYMENT.md            # Deployment guide
    ├── ENVIRONMENT_VARIABLES.md # Environment reference
    ├── MONITORING.md            # Monitoring setup
    ├── nginx/                   # Nginx configuration
    ├── prometheus/              # Prometheus configuration
    ├── alertmanager/            # AlertManager configuration
    └── scripts/                 # Deployment scripts
        ├── deploy.sh
        ├── backup-database.sh
        ├── restore-database.sh
        └── smoke-tests.sh
```

## API Documentation

### Interactive Documentation

Once the backend is running, access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Core API Endpoints

**Sessions:**
```
POST   /api/v1/sessions               # Create learning session
GET    /api/v1/sessions/{id}          # Get session details
DELETE /api/v1/sessions/{id}          # Delete session
```

**Graph:**
```
POST   /api/v1/sessions/{id}/graph/generate   # Generate prerequisite graph
GET    /api/v1/sessions/{id}/graph            # Get graph data
```

**Diagnosis:**
```
POST   /api/v1/sessions/{id}/diagnosis/start   # Start diagnostic assessment
GET    /api/v1/sessions/{id}/diagnosis/current # Get current question
POST   /api/v1/sessions/{id}/diagnosis/answer  # Submit answer
```

**Root Gap:**
```
GET    /api/v1/sessions/{id}/root-gap         # Get root gap analysis
```

**Tutor:**
```
POST   /api/v1/sessions/{id}/tutor/messages   # Send message to tutor
GET    /api/v1/sessions/{id}/tutor/messages   # Get conversation history
POST   /api/v1/sessions/{id}/tutor/stream     # Stream response (SSE)
```

**Teach-Back:**
```
POST   /api/v1/sessions/{id}/teachback        # Submit teach-back explanation
```

**Health:**
```
GET    /api/v1/health                         # Basic health check
GET    /api/v1/health/db                      # Database connectivity check
```

### API Error Format

All errors follow this structure:

```json
{
  "error": {
    "code": "GRAPH_VALIDATION_FAILED",
    "message": "Generated prerequisite graph contains a cycle.",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "details": {
      "cycle": ["functions", "recursion", "call-stack", "functions"]
    }
  }
}
```

## Development

### Backend Development

```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # or: poetry shell

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_mastery_service.py

# Run property tests only
pytest tests/property/

# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/

# Create database migration
alembic revision --autogenerate -m "add new field to concepts"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Start development server
uvicorn app.main:app --reload --port 8000

# Start with debug logging
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run type checking
npm run type-check

# Run linting
npm run lint

# Run tests (if implemented)
npm test

# Run E2E tests
npx playwright test
```

### Database Management

```bash
# Connect to database
docker-compose exec postgres psql -U rootlearn -d rootlearn

# View logs
docker-compose logs -f postgres

# Backup database
docker-compose exec postgres pg_dump -U rootlearn rootlearn > backup.sql

# Restore database
docker-compose exec -T postgres psql -U rootlearn rootlearn < backup.sql

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

## Testing

### Testing Philosophy

RootLearn uses a **dual testing approach**:

1. **Unit Tests**: Verify specific examples, edge cases, and error conditions
2. **Property-Based Tests**: Verify universal properties across many generated inputs

### Running Tests

**All tests:**
```bash
cd backend
pytest
```

**With coverage:**
```bash
pytest --cov=app --cov-report=html tests/
open htmlcov/index.html
```

**Specific test categories:**
```bash
pytest tests/unit/              # Unit tests only
pytest tests/property/          # Property-based tests
pytest tests/integration/       # Integration tests
```

**Specific test file:**
```bash
pytest tests/property/test_mastery_properties.py -v
```

### Test Organization

**Unit Tests** (`tests/unit/`):
- `test_session_service.py` - Session CRUD operations
- `test_mastery_service.py` - Mastery calculations
- `test_root_gap_service.py` - Gap scoring
- `test_ai_provider.py` - AI provider abstraction

**Property Tests** (`tests/property/`):
- `test_mastery_properties.py` - Properties 19-25 (deterministic mastery)
- `test_root_gap_properties.py` - Properties 29-32 (gap detection)
- `test_graph_properties.py` - Properties 6-9 (graph validation)
- `test_diagnostic_properties.py` - Properties 13-18 (diagnosis)
- `test_api_contracts.py` - Properties 73-77 (API contracts)

**Integration Tests** (`tests/integration/`):
- `test_complete_learning_loop.py` - End-to-end learning flow
- `test_diagnosis_endpoints.py` - Diagnostic API integration
- `test_root_gap_endpoints.py` - Root gap API integration

### Property-Based Testing

RootLearn uses [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing.

**Example property test:**
```python
from hypothesis import given, strategies as st

@given(
    diagnostic_score=st.floats(min_value=0.0, max_value=1.0),
    practice_score=st.floats(min_value=0.0, max_value=1.0),
    teachback_score=st.floats(min_value=0.0, max_value=1.0),
)
def test_mastery_bounds(diagnostic_score, practice_score, teachback_score):
    """Property 22: Mastery scores remain between 0 and 1"""
    mastery = calculate_mastery(diagnostic_score, practice_score, teachback_score)
    assert 0.0 <= mastery <= 1.0
```

**Configuration:**
- Minimum 100 iterations per property test
- Each test references its design document property number
- Tests are tagged with feature and property information

### Writing Tests

**Guidelines:**
- Write tests alongside implementation
- Property tests for deterministic algorithms
- Unit tests for specific examples and edge cases
- Integration tests for API contracts
- Mock external dependencies (AI providers)
- Use realistic test data

## Deployment

### Quick Deployment (Docker Compose)

```bash
# 1. Configure environment
cp .env.production.example .env.production
# Edit .env.production with your values

# 2. Deploy
./deployment/scripts/deploy.sh

# 3. Monitor
docker-compose -f docker-compose.prod.yml logs -f
```

### Manual Deployment

See comprehensive deployment documentation:
- **[Deployment Guide](deployment/DEPLOYMENT.md)** - Complete deployment instructions
- **[Environment Variables](deployment/ENVIRONMENT_VARIABLES.md)** - Configuration reference
- **[Monitoring Setup](deployment/MONITORING.md)** - Observability configuration

### Database Migration Strategy

**Philosophy:**
- Forward-only migrations (never modify existing migrations)
- Backward-compatible changes for zero-downtime deployments
- Always backup before migration
- Test migrations in staging first

**Commands:**
```bash
# Review pending migrations
alembic current
alembic history

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Create new migration
alembic revision --autogenerate -m "description"
```

### Production Checklist

Before deploying to production:

- [ ] Set strong passwords for all services
- [ ] Configure SSL/TLS certificates
- [ ] Set `ALLOWED_ORIGINS` to production domain only
- [ ] Enable all security headers in Nginx
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerts (Prometheus, Grafana)
- [ ] Configure automated backups
- [ ] Test restore procedure
- [ ] Review and update firewall rules
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `LOG_LEVEL=INFO` or `WARNING`
- [ ] Use secrets management (not `.env` files in production)

### Monitoring

**Health Checks:**
```bash
curl https://api.yourdomain.com/api/v1/health
curl https://api.yourdomain.com/api/v1/health/db
```

**Metrics Endpoint:**
```bash
curl https://api.yourdomain.com/metrics
```

**Key Metrics Tracked:**
- API request latency (p50, p95, p99)
- AI operation latency
- Session completion rate
- Diagnostic questions per session
- Average mastery improvement
- AI provider errors and costs
- Database connection pool usage

**Logging:**
- Structured JSON logs with correlation IDs
- Log aggregation to stdout/stderr
- Centralized logging (optional: ELK, Loki)
- Error tracking (optional: Sentry)

## Features

### Current Features (✅ Implemented)

**Core Learning Loop:**
- ✅ Session creation with target concept identification
- ✅ AI-powered prerequisite graph generation
- ✅ Graph validation (DAG, size limits, structural constraints)
- ✅ Adaptive diagnostic assessment (max 6 questions)
- ✅ Deterministic mastery calculation (3 evidence types)
- ✅ Root gap detection with explainable scoring
- ✅ Socratic tutoring with progressive hints
- ✅ Teach-back evaluation
- ✅ Learning path progression (topological ordering)
- ✅ Session state machine with controlled transitions

**Technical Features:**
- ✅ Multi-provider AI support (OpenAI, Anthropic, Gemini)
- ✅ AI output validation with retry logic
- ✅ Comprehensive AI operation logging
- ✅ Structured logging with correlation IDs
- ✅ Health check endpoints
- ✅ Database migrations with Alembic
- ✅ Property-based testing suite
- ✅ API error handling with structured responses
- ✅ Interactive API documentation

**UI Components:**
- ✅ Landing page with session creation
- ✅ Interactive knowledge graph visualization (React Flow)
- ✅ Diagnostic question interface
- ✅ Root gap explanation card
- ✅ Socratic tutor chat interface
- ✅ Teach-back submission panel
- ✅ Mastery bars and progress indicators
- ✅ Mastery history timeline

### Roadmap (🚧 Planned)

**Phase 2 (Post-MVP):**
- 🚧 User authentication and authorization
- 🚧 Rate limiting per user
- 🚧 Session history and analytics
- 🚧 Export learning reports
- 🚧 Voice input/output for accessibility
- 🚧 PDF/document context upload
- 🚧 Mobile-responsive UI improvements

**Phase 3 (Scale):**
- 🚧 Teacher-created concept graphs
- 🚧 Course-level learning plans
- 🚧 Spaced repetition review system
- 🚧 Multi-language support
- 🚧 Social features (share progress)

**Phase 4 (Advanced):**
- 🚧 Coding sandbox integration
- 🚧 Math visualization tools
- 🚧 Specialized evaluators per domain
- 🚧 Adaptive difficulty tuning

### Explicit Non-Goals

These features are intentionally **not** included to maintain focus:

- ❌ Social features or peer ranking
- ❌ Classroom or teacher dashboards
- ❌ Gamification or badges
- ❌ Payment systems
- ❌ Generic chatbot modes
- ❌ Document-to-course generation
- ❌ Multi-tenant organization management
- ❌ Exam management or grading systems

## Configuration

### Backend Environment Variables

Create `backend/.env` from `.env.example`:

```env
# Required
DATABASE_URL=postgresql+asyncpg://rootlearn:rootlearn@localhost:5432/rootlearn
AI_PROVIDER=openai  # or: anthropic, gemini
OPENAI_API_KEY=sk-your-key-here

# Application
ENVIRONMENT=development  # or: staging, production
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
API_V1_PREFIX=/api/v1

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
MAX_SESSIONS_PER_HOUR=20
MAX_TUTOR_TURNS_PER_HOUR=120
MAX_TEACHBACKS_PER_HOUR=40
MAX_AI_CALLS_PER_SESSION=30

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SECURE=true  # true in production

# Optional: Other AI providers
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_API_KEY=your-google-key-here

# Optional: Monitoring
SENTRY_DSN=https://your-dsn@sentry.io/project
```

### Frontend Environment Variables

Create `frontend/.env.local` from `.env.local.example`:

```env
# Required
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional
NEXT_PUBLIC_SENTRY_DSN=https://your-dsn@sentry.io/project
```

### Configuration Guide

**Database Connection:**
- Use async driver: `postgresql+asyncpg://`
- Connection pooling is configured automatically
- For production, use managed PostgreSQL service

**AI Provider Selection:**
- Set `AI_PROVIDER` to: `openai`, `anthropic`, or `gemini`
- Provide corresponding API key
- System automatically uses configured provider

**Security:**
- Generate secrets: `openssl rand -hex 32`
- Use environment-specific origins in `ALLOWED_ORIGINS`
- Enable secure cookies in production
- Never commit `.env` files to version control

**Performance:**
- Adjust rate limits based on your needs
- Monitor AI costs and adjust limits accordingly
- Use connection pooling for database

## Troubleshooting

### Common Issues

#### Database Connection Errors

**Problem:** `sqlalchemy.exc.OperationalError: could not connect to server`

**Solutions:**
```bash
# Check if PostgreSQL is running
docker-compose ps
docker-compose logs postgres

# Test connectivity
docker-compose exec postgres pg_isready -U rootlearn

# Verify DATABASE_URL in .env
cat backend/.env | grep DATABASE_URL

# Restart PostgreSQL
docker-compose restart postgres
```

#### AI Provider Errors

**Problem:** `AI provider authentication failed`

**Solutions:**
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Check .env file
cat backend/.env | grep API_KEY

# Test provider connection
cd backend
python -c "from app.ai.factory import get_ai_provider; provider = get_ai_provider(); print('OK')"
```

#### Port Already in Use

**Problem:** `Address already in use` when starting services

**Solutions:**
```bash
# Backend (change from default 8000)
uvicorn app.main:app --reload --port 8001

# Frontend (change from default 3000)
PORT=3001 npm run dev

# Find process using port
lsof -i :8000
netstat -tuln | grep 8000
```

#### Module Not Found

**Problem:** `ModuleNotFoundError` or `ImportError`

**Solutions:**
```bash
# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
rm -rf node_modules .next
npm install
```

#### Migration Errors

**Problem:** `alembic.util.exc.CommandError: Can't locate revision`

**Solutions:**
```bash
# Check current database version
alembic current

# Check migration history
alembic history

# Stamp database at head (if clean install)
alembic stamp head

# Apply migrations
alembic upgrade head
```

#### High Memory Usage

**Problem:** Backend consuming excessive memory

**Solutions:**
```bash
# Check container stats
docker stats

# Restart services
docker-compose restart backend

# Check for memory leaks in logs
docker-compose logs backend | grep -i "memory"

# Adjust memory limits in docker-compose.yml
# deploy.resources.limits.memory: 2G
```

### Debug Mode

Enable detailed logging temporarily:

```bash
# Backend
LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# Or set in .env
LOG_LEVEL=DEBUG

# View structured logs
docker-compose logs -f backend | jq
```

### Getting Help

- **Documentation**: See `docs/` and `.kiro/specs/` directories
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **Database Status**: http://localhost:8000/api/v1/health/db

## Contributing

### Development Workflow

1. **Check the implementation plan**: `.kiro/specs/rootlearn-knowledge-debugger/tasks.md`
2. **Each task references specific requirements**: See `.kiro/specs/rootlearn-knowledge-debugger/requirements.md`
3. **Review design decisions**: See `.kiro/specs/rootlearn-knowledge-debugger/design.md`
4. **Write tests alongside implementation**
5. **Ensure all tests pass before committing**
6. **Follow code quality standards**

### Code Quality Standards

**Backend:**
- Black formatting: `black app/ tests/`
- Ruff linting: `ruff check app/ tests/`
- Type hints for all functions
- Docstrings for public APIs
- Pydantic models for validation

**Frontend:**
- ESLint: `npm run lint`
- TypeScript strict mode
- Prettier formatting (optional)
- React hooks best practices
- Accessibility compliance (WCAG 2.1 AA)

**Testing:**
- Property-based tests for correctness properties
- Unit tests for specific examples
- Integration tests for API contracts
- Minimum 80% code coverage goal

### Pull Request Guidelines

1. Create feature branch from `main`
2. Write descriptive commit messages
3. Add tests for new functionality
4. Update documentation as needed
5. Ensure all tests pass
6. Request review from maintainers

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Examples:**
```
feat(mastery): implement weight renormalization for partial evidence
fix(graph): prevent cycles in prerequisite graphs
docs(api): add examples to session endpoints
test(diagnostic): add property tests for concept selection
```

## Documentation

### Core Documentation

- **[README.md](README.md)** - This file (overview and getting started)
- **[Requirements](. kiro/specs/rootlearn-knowledge-debugger/requirements.md)** - Formal EARS requirements
- **[Design](. kiro/specs/rootlearn-knowledge-debugger/design.md)** - System design and architecture
- **[Tasks](. kiro/specs/rootlearn-knowledge-debugger/tasks.md)** - Implementation plan with task list

### Component Documentation

- **[Backend README](backend/README.md)** - Backend setup and development
- **[Frontend README](frontend/README.md)** - Frontend setup and development
- **[Deployment Guide](deployment/DEPLOYMENT.md)** - Production deployment
- **[Environment Variables](deployment/ENVIRONMENT_VARIABLES.md)** - Configuration reference
- **[Monitoring Setup](deployment/MONITORING.md)** - Observability and alerts

### API Documentation

- **Swagger UI**: http://localhost:8000/docs (interactive)
- **ReDoc**: http://localhost:8000/redoc (documentation)

### Additional Resources

- **Architecture Diagram**: See [Architecture](#architecture) section
- **Database Schema**: See `.kiro/specs/rootlearn-knowledge-debugger/design.md`
- **AI Prompts**: See `backend/app/ai/prompts.py`
- **Property List**: See design document Correctness Properties section

## License

[Your License Here - Add appropriate license]

## Contact

[Your Contact Information - Add maintainer contact details]

---

**Built with ❤️ using AI-powered development** Knowledge Debugger

An AI-powered knowledge debugger that identifies root prerequisite gaps in a learner's understanding and provides adaptive Socratic tutoring.

## Architecture

RootLearn consists of two main components:

- **Backend**: FastAPI-based REST API (Python 3.11+)
- **Frontend**: Next.js 15+ React application (TypeScript)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 16+ (or Docker)
- Poetry (Python package manager)

### 1. Start PostgreSQL

Using Docker:
```bash
docker-compose up -d postgres
```

Or use your local PostgreSQL installation and create a database named `rootlearn`.

### 2. Setup Backend

```bash
cd backend
poetry install
cp .env.example .env
# Edit .env with your configuration (database URL, AI provider keys)
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

API Documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. Setup Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local if needed (defaults to localhost:8000)
npm run dev
```

Frontend will be available at: http://localhost:3000

## Project Structure

```
rootlearn/
├── backend/           # FastAPI backend
│   ├── alembic/      # Database migrations
│   ├── app/          # Application code
│   │   ├── routes/   # API endpoints
│   │   ├── services/ # Business logic
│   │   └── models/   # Database models
│   └── tests/        # Backend tests
├── frontend/         # Next.js frontend
│   └── src/
│       ├── app/      # Next.js App Router
│       ├── components/ # React components
│       └── lib/      # Utilities and API client
└── docker-compose.yml # PostgreSQL setup
```

## Key Features

- **Session Management**: Create and manage learning sessions
- **Prerequisite Graph Generation**: AI-generated concept dependency graphs
- **Adaptive Diagnostic Assessment**: Targeted questioning to identify knowledge gaps
- **Root Gap Detection**: Identify the most impactful prerequisite to learn
- **Socratic Tutoring**: Progressive hint-based teaching
- **Teach-Back Verification**: Verify understanding through explanation
- **Deterministic Mastery Calculation**: Transparent progress tracking
- **Visual Knowledge Graph**: Interactive graph visualization with React Flow

## Development

### Backend

```bash
cd backend
poetry run pytest                    # Run tests
poetry run black .                   # Format code
poetry run ruff check .              # Lint code
poetry run alembic revision -m "msg" # Create migration
```

### Frontend

```bash
cd frontend
npm run dev         # Development server
npm run build       # Production build
npm run type-check  # TypeScript checking
npm run lint        # ESLint
```

## Health Checks

Backend provides health check endpoints:

- Basic: `GET /api/v1/health`
- Database: `GET /api/v1/health/db`

## Environment Variables

### Backend (.env)

```env
DATABASE_URL=postgresql+asyncpg://rootlearn:rootlearn@localhost:5432/rootlearn
AI_PROVIDER=openai
OPENAI_API_KEY=your_key_here
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## License

MIT
