# RootLearn Knowledge Debugger

An AI-powered system that identifies root prerequisite gaps in a learner's understanding, teaches missing concepts through adaptive Socratic guidance, and verifies understanding with teach-back evaluation.

## Overview

RootLearn differs from traditional AI tutors by diagnosing **why** a learner cannot understand a concept and addressing the foundational knowledge gap. The system:

1. **Analyzes** the target concept and builds a prerequisite knowledge graph
2. **Diagnoses** understanding through adaptive questioning
3. **Identifies** the root gap blocking comprehension
4. **Teaches** using Socratic guidance with progressive hints
5. **Verifies** understanding through teach-back explanations
6. **Tracks** mastery deterministically with transparent scoring

## Architecture

### Design Principles

- **AI for semantic tasks**: Concept identification, question generation, answer evaluation
- **Deterministic logic for learning state**: Mastery calculation, root-gap detection, learning path progression
- **Separation ensures**: Explainability, testability, reproducibility, and resistance to model inconsistency

### Technology Stack

**Backend:**
- Python 3.11+ with FastAPI
- SQLAlchemy 2 (async) with PostgreSQL
- Alembic for migrations
- NetworkX for graph algorithms
- Structured logging with correlation IDs

**Frontend:**
- Next.js 15+ with React 18
- TypeScript (strict mode)
- Tailwind CSS
- React Flow for knowledge graph visualization
- TanStack Query for state management

**Infrastructure:**
- PostgreSQL 16+ database
- Docker & Docker Compose for local development
- Multi-provider AI support (OpenAI, Anthropic, Gemini)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+ (or Docker)
- Docker & Docker Compose (optional, for database)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd rootlearn
```

### 2. Start the Database

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
# Edit .env and set your AI provider API key

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

### 4. Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Verify NEXT_PUBLIC_API_URL points to backend

# Start the development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Project Structure

```
rootlearn/
├── backend/              # FastAPI backend
│   ├── alembic/         # Database migrations
│   ├── app/
│   │   ├── main.py      # Application entry point
│   │   ├── config.py    # Configuration management
│   │   ├── database.py  # Database setup
│   │   ├── logging_config.py  # Structured logging
│   │   ├── middleware.py      # Request middleware
│   │   └── routes/      # API endpoints
│   ├── tests/           # Backend tests
│   └── pyproject.toml   # Python dependencies
├── frontend/            # Next.js frontend
│   ├── src/
│   │   ├── app/        # Next.js App Router
│   │   └── lib/        # Shared utilities
│   ├── public/         # Static assets
│   └── package.json    # Node dependencies
├── .kiro/
│   └── specs/          # Feature specifications
│       └── rootlearn-knowledge-debugger/
│           ├── requirements.md  # Formal requirements
│           ├── design.md        # System design
│           └── tasks.md         # Implementation plan
└── docker-compose.yml  # Local development setup
```

## API Documentation

Once the backend is running, access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Health Check Endpoints

```bash
# Basic health check
curl http://localhost:8000/api/v1/health

# Database connectivity check
curl http://localhost:8000/api/v1/health/db
```

## Development

### Backend Development

```bash
cd backend

# Run tests
pytest

# Run tests with coverage
pytest --cov=app tests/

# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Create database migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Frontend Development

```bash
cd frontend

# Run type checking
npm run type-check

# Run linting
npm run lint

# Build for production
npm run build

# Start production server
npm run start
```

## Configuration

### Backend Environment Variables

Create `backend/.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://rootlearn:rootlearn@localhost:5432/rootlearn

# AI Provider (openai, anthropic, or gemini)
AI_PROVIDER=openai
OPENAI_API_KEY=your_key_here

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
API_V1_PREFIX=/api/v1

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
```

### Frontend Environment Variables

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Features

### Core Capabilities

✅ **Session Management**: Create and manage learning sessions  
✅ **Target Concept Identification**: AI-powered concept extraction  
✅ **Prerequisite Graph Generation**: DAG validation with NetworkX  
✅ **Adaptive Diagnostic Assessment**: Intelligent question selection  
✅ **Deterministic Mastery Calculation**: Transparent scoring  
✅ **Root Gap Detection**: Identify blocking prerequisites  
✅ **Socratic Tutoring**: Progressive hint escalation  
✅ **Teach-Back Verification**: Explanation-based validation  
✅ **Learning Path Progression**: Topological ordering  
✅ **Structured Logging**: Correlation IDs and JSON logs  
✅ **Health Check Endpoints**: Application and database monitoring

### Upcoming Features

🚧 Database models and migrations (Task 2)  
🚧 AI provider abstraction layer (Task 3)  
🚧 AI output validation and logging (Task 4)  
🚧 Interactive knowledge graph visualization (Task 17)  
🚧 Full diagnostic and tutoring UI (Tasks 18-20)

## Testing

### Backend Tests

Property-based testing with Hypothesis:

```bash
cd backend
pytest tests/
```

### Test Coverage

- Unit tests for business logic
- Property tests for correctness guarantees
- Integration tests for API endpoints
- End-to-end tests for complete workflows

## Contributing

### Workflow

1. Check the implementation plan: `.kiro/specs/rootlearn-knowledge-debugger/tasks.md`
2. Each task references specific requirements and design decisions
3. Write tests alongside implementation
4. Ensure all tests pass before committing

### Code Quality Standards

- **Backend**: Black formatting, Ruff linting, type hints
- **Frontend**: ESLint, TypeScript strict mode, Prettier
- **Tests**: Property-based tests for correctness properties

## Documentation

- **Requirements**: `.kiro/specs/rootlearn-knowledge-debugger/requirements.md`
- **Design**: `.kiro/specs/rootlearn-knowledge-debugger/design.md`
- **Tasks**: `.kiro/specs/rootlearn-knowledge-debugger/tasks.md`
- **Backend README**: `backend/README.md`
- **Frontend README**: `frontend/README.md`

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres

# Test connectivity
curl http://localhost:8000/api/v1/health/db
```

### Port Conflicts

If ports are already in use:

```bash
# Backend (default 8000)
uvicorn app.main:app --reload --port 8001

# Frontend (default 3000)
PORT=3001 npm run dev
```

### Module Not Found

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

## License

[Your License Here]

## Contact

[Your Contact Information] Knowledge Debugger

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
