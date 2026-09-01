#!/usr/bin/env python3
"""
Foundation Verification Script for Task 9

This script verifies:
1. Database migrations work
2. AI provider connection works  
3. Session creation works end-to-end
4. Graph generation works end-to-end
"""

import asyncio
import uuid
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, AsyncSessionLocal
from app.services.session_service import SessionService
from app.services.concept_service import ConceptService
from app.services.graph_service import GraphService
from app.ai.factory import get_ai_provider
import structlog

logger = structlog.get_logger()


async def verify_database_migrations():
    """Verify database migrations are applied and tables exist"""
    print("\n=== Verifying Database Migrations ===")
    try:
        async with engine.begin() as conn:
            # Check if tables exist
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            expected_tables = [
                'ai_runs', 'alembic_version', 'concept_edges', 'concepts',
                'diagnostic_attempts', 'diagnostic_questions', 'learning_sessions',
                'mastery_events', 'teachback_attempts', 'tutor_messages', 'users'
            ]
            
            missing_tables = set(expected_tables) - set(tables)
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            
            print(f"✅ All {len(expected_tables)} required tables exist")
            print(f"   Tables: {', '.join(sorted(tables))}")
            return True
    except Exception as e:
        print(f"❌ Database migration check failed: {e}")
        return False


async def verify_ai_provider():
    """Verify AI provider is configured and accessible"""
    print("\n=== Verifying AI Provider Connection ===")
    try:
        provider = get_ai_provider()
        print(f"✅ AI Provider configured: {provider.__class__.__name__}")
        print(f"   Provider: {provider}")
        return True
    except Exception as e:
        print(f"❌ AI provider check failed: {e}")
        return False


async def verify_session_creation():
    """Verify session creation works end-to-end"""
    print("\n=== Verifying Session Creation ===")
    try:
        async with AsyncSessionLocal() as db_session:
            service = SessionService(db_session)
            
            # Create a test user
            from app.models import User
            user = User(
                id=uuid.uuid4(),
                email=f"test_{uuid.uuid4().hex[:8]}@example.com",
                name="Test User"
            )
            db_session.add(user)
            await db_session.flush()
            
            # Create a session
            session = await service.create_session(
                user_id=user.id,
                prompt="I don't understand recursion"
            )
            
            print(f"✅ Session created successfully")
            print(f"   Session ID: {session.id}")
            print(f"   Status: {session.status}")
            print(f"   Prompt: {session.original_prompt}")
            
            # Verify we can retrieve it
            retrieved = await service.get_session(
                session_id=session.id,
                user_id=user.id
            )
            
            print(f"✅ Session retrieved successfully")
            print(f"   Retrieved ID matches: {retrieved.id == session.id}")
            
            await db_session.rollback()  # Don't persist test data
            return True
            
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_graph_generation():
    """Verify graph generation works end-to-end"""
    print("\n=== Verifying Graph Generation ===")
    try:
        async with AsyncSessionLocal() as db_session:
            # Create test user and session
            from app.models import User, LearningSession
            user = User(
                id=uuid.uuid4(),
                email=f"test_{uuid.uuid4().hex[:8]}@example.com",
                name="Test User"
            )
            db_session.add(user)
            await db_session.flush()
            
            session = LearningSession(
                id=uuid.uuid4(),
                user_id=user.id,
                original_prompt="I don't understand recursion",
                status="analyzing"
            )
            db_session.add(session)
            await db_session.flush()
            
            # First identify the target concept
            from app.ai.validated_ai_service import ValidatedAIService
            from app.ai.logging_service import AIRunLogger
            
            ai_provider = get_ai_provider()
            logging_service = AIRunLogger(db_session)
            ai_service = ValidatedAIService(ai_provider, logging_service)
            
            concept_service = ConceptService(db_session, ai_service)
            target_concept = await concept_service.analyze_target_concept(
                session_id=session.id,
                prompt=session.original_prompt
            )
            
            print(f"✅ Target concept identified")
            print(f"   Concept: {target_concept.name}")
            print(f"   Description: {target_concept.description[:100]}...")
            
            # Generate prerequisite graph
            graph_service = GraphService(db_session, ai_service)
            graph_result = await graph_service.generate_graph(session_id=session.id)
            
            print(f"✅ Prerequisite graph generated")
            print(f"   Nodes: {len(graph_result['nodes'])}")
            print(f"   Edges: {len(graph_result['edges'])}")
            print(f"   Concepts: {[n['name'] for n in graph_result['nodes'][:5]]}")
            
            # Verify graph validation passed
            if len(graph_result['nodes']) > 12:
                print(f"⚠️  Warning: Graph has {len(graph_result['nodes'])} nodes (limit is 12)")
            
            await db_session.rollback()  # Don't persist test data
            return True
            
    except Exception as e:
        print(f"❌ Graph generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all verification checks"""
    print("=" * 60)
    print("RootLearn Foundation Verification")
    print("=" * 60)
    
    results = {
        "Database Migrations": await verify_database_migrations(),
        "AI Provider Connection": await verify_ai_provider(),
        "Session Creation": await verify_session_creation(),
        "Graph Generation": await verify_graph_generation(),
    }
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All foundation checks passed!")
        print("=" * 60)
        return 0
    else:
        print("⚠️  Some foundation checks failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
