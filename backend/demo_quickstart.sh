#!/bin/bash
# Quick start script for RootLearn demo

set -e

echo "======================================"
echo "RootLearn Demo Quick Start"
echo "======================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Virtual environment not activated!"
    echo "Please run: source venv/bin/activate"
    exit 1
fi

echo "✓ Virtual environment activated"

# Check if database is running
echo ""
echo "Checking PostgreSQL database..."
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running!"
    echo "Please start PostgreSQL or run: docker-compose up -d"
    exit 1
fi

echo "✓ PostgreSQL is running"

# Run migrations
echo ""
echo "Running database migrations..."
alembic upgrade head
echo "✓ Migrations complete"

# Seed demo data
echo ""
echo "Seeding demo data..."
python seed_demo.py

# Get the session ID from the database
echo ""
echo "Retrieving demo session information..."
SESSION_ID=$(python -c "
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User, LearningSession

async def get_session_id():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(LearningSession)
            .join(User)
            .where(User.email == 'demo@rootlearn.example')
            .order_by(LearningSession.created_at.desc())
        )
        session = result.scalar_one_or_none()
        if session:
            print(session.id)

asyncio.run(get_session_id())
")

if [ -z "$SESSION_ID" ]; then
    echo "❌ Could not retrieve demo session ID"
    exit 1
fi

echo ""
echo "======================================"
echo "Demo Ready!"
echo "======================================"
echo ""
echo "Demo User: demo@rootlearn.example"
echo "Session ID: $SESSION_ID"
echo ""
echo "To start the backend server:"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Example API calls:"
echo "  # Get session"
echo "  curl http://localhost:8000/api/v1/sessions/$SESSION_ID"
echo ""
echo "  # Get graph"
echo "  curl http://localhost:8000/api/v1/sessions/$SESSION_ID/graph"
echo ""
echo "  # Get root gap"
echo "  curl http://localhost:8000/api/v1/sessions/$SESSION_ID/root-gap"
echo ""
echo "Or open the frontend and use session ID: $SESSION_ID"
echo ""
