"""Cross-platform demo quickstart script for RootLearn.

This script:
1. Checks prerequisites (database, migrations)
2. Seeds demo data
3. Provides quick access information

Usage:
    python demo_quickstart.py
"""
import asyncio
import subprocess
import sys
import os

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User, LearningSession


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_step(text: str, success: bool = True):
    """Print a step with status indicator."""
    symbol = "✓" if success else "❌"
    print(f"{symbol} {text}")


async def get_demo_session_id() -> str | None:
    """Retrieve the demo session ID from the database."""
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(LearningSession)
                .join(User)
                .where(User.email == "demo@rootlearn.example")
                .order_by(LearningSession.created_at.desc())
            )
            session = result.scalar_one_or_none()
            return str(session.id) if session else None
    except Exception as e:
        print(f"Error retrieving session: {e}")
        return None


def check_virtual_env() -> bool:
    """Check if virtual environment is activated."""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def check_database() -> bool:
    """Check if PostgreSQL is accessible."""
    try:
        # Try to import asyncpg as a quick check
        import asyncpg
        return True
    except ImportError:
        return False


def run_migrations() -> bool:
    """Run Alembic migrations."""
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Migration error: {e}")
        return False


def seed_demo_data() -> bool:
    """Run the demo seed script."""
    try:
        result = subprocess.run(
            [sys.executable, "seed_demo.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Seed error: {e}")
        return False


async def main():
    """Run the demo quickstart."""
    print_header("RootLearn Demo Quick Start")
    
    # Check virtual environment
    if check_virtual_env():
        print_step("Virtual environment activated")
    else:
        print_step("Virtual environment not activated!", success=False)
        print("\nPlease activate virtual environment:")
        print("  source venv/bin/activate  (Linux/Mac)")
        print("  venv\\Scripts\\activate     (Windows)")
        return 1
    
    # Check database dependencies
    if check_database():
        print_step("Database dependencies available")
    else:
        print_step("Database dependencies missing!", success=False)
        print("\nPlease install requirements:")
        print("  pip install -r requirements.txt")
        return 1
    
    # Run migrations
    print("\nRunning database migrations...")
    if run_migrations():
        print_step("Migrations complete")
    else:
        print_step("Migration failed!", success=False)
        print("\nPlease check:")
        print("  - PostgreSQL is running (docker-compose up -d)")
        print("  - DATABASE_URL is set correctly in .env")
        return 1
    
    # Seed demo data
    print("\nSeeding demo data...")
    if not seed_demo_data():
        print_step("Seeding failed!", success=False)
        return 1
    
    # Get session ID
    print("\nRetrieving demo session information...")
    session_id = await get_demo_session_id()
    
    if not session_id:
        print_step("Could not retrieve demo session ID", success=False)
        return 1
    
    # Print success information
    print_header("Demo Ready!")
    print(f"\nDemo User: demo@rootlearn.example")
    print(f"Session ID: {session_id}")
    
    print("\n" + "-" * 60)
    print("To start the backend server:")
    print("  uvicorn app.main:app --reload")
    
    print("\n" + "-" * 60)
    print("Example API calls:")
    print(f"\n  # Get session")
    print(f"  curl http://localhost:8000/api/v1/sessions/{session_id}")
    
    print(f"\n  # Get graph")
    print(f"  curl http://localhost:8000/api/v1/sessions/{session_id}/graph")
    
    print(f"\n  # Get root gap")
    print(f"  curl http://localhost:8000/api/v1/sessions/{session_id}/root-gap")
    
    print(f"\n  # Get tutor messages")
    print(f"  curl http://localhost:8000/api/v1/sessions/{session_id}/tutor/messages")
    
    print("\n" + "-" * 60)
    print(f"Frontend: Open your browser and use session ID: {session_id}")
    print()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
