"""Demo seed data for RootLearn presentations and testing.

This script creates a pre-built demo scenario for "I don't understand recursion"
with a complete prerequisite graph, diagnostic questions, and example interactions.

Usage:
    python seed_demo.py

The script is idempotent - running it multiple times will not create duplicates.
"""
import asyncio
import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    User,
    LearningSession,
    Concept,
    ConceptEdge,
    DiagnosticQuestion,
    DiagnosticAttempt,
    TutorMessage,
    TeachBackAttempt,
    MasteryEvent,
)


# Demo user credentials
DEMO_USER_EMAIL = "demo@rootlearn.example"
DEMO_USER_NAME = "Demo User"

# Recursion prerequisite graph structure
RECURSION_GRAPH = {
    "target": {
        "slug": "recursion",
        "name": "Recursion",
        "description": "A programming technique where a function calls itself to solve smaller instances of the same problem",
        "is_target": True,
    },
    "concepts": [
        {
            "slug": "function-calls",
            "name": "Function Calls",
            "description": "Understanding how functions are invoked and how control flow works when calling functions",
        },
        {
            "slug": "call-stack",
            "name": "Call Stack",
            "description": "The data structure that manages function execution order and stores local variables",
        },
        {
            "slug": "base-case",
            "name": "Base Case",
            "description": "The terminating condition in recursion that prevents infinite loops",
        },
        {
            "slug": "recursive-case",
            "name": "Recursive Case",
            "description": "The part of a recursive function that makes a recursive call with a simpler problem",
        },
        {
            "slug": "problem-decomposition",
            "name": "Problem Decomposition",
            "description": "Breaking down a large problem into smaller, similar subproblems",
        },
        {
            "slug": "state-transitions",
            "name": "State Transitions",
            "description": "How program state changes between recursive calls and returns",
        },
    ],
    "edges": [
        # Function calls is a prerequisite for call stack
        {"source": "function-calls", "target": "call-stack", "weight": 0.9},
        # Call stack is a prerequisite for understanding recursion
        {"source": "call-stack", "target": "recursion", "weight": 0.95},
        # Problem decomposition is needed for recursion
        {"source": "problem-decomposition", "target": "recursion", "weight": 0.85},
        # Base case and recursive case both needed for recursion
        {"source": "base-case", "target": "recursion", "weight": 0.90},
        {"source": "recursive-case", "target": "recursion", "weight": 0.90},
        # Call stack needed to understand recursive case
        {"source": "call-stack", "target": "recursive-case", "weight": 0.80},
        # Problem decomposition needed for recursive case
        {"source": "problem-decomposition", "target": "recursive-case", "weight": 0.75},
        # State transitions build on call stack
        {"source": "call-stack", "target": "state-transitions", "weight": 0.70},
        # State transitions help understand recursion
        {"source": "state-transitions", "target": "recursion", "weight": 0.60},
    ],
}

# Diagnostic questions for each concept
DIAGNOSTIC_QUESTIONS = {
    "function-calls": {
        "question_text": "Explain what happens when you call a function in Python. What information needs to be tracked?",
        "question_type": "reasoning",
        "rubric": {
            "required_points": [
                "Function execution begins",
                "Parameters are passed",
                "Local variables are created",
                "Control returns to caller when done",
            ],
            "max_score": 1.0,
        },
        "expected_good_answer": "When you call a function, the program jumps to that function's code. The arguments are passed as parameters, local variables are created in the function's scope, the function executes, and then control returns to where the function was called.",
        "expected_weak_answer": "The function runs.",
    },
    "call-stack": {
        "question_text": "What is the call stack and why is it important? What would happen if functions didn't use a stack?",
        "question_type": "reasoning",
        "rubric": {
            "required_points": [
                "Stack stores function call information",
                "LIFO (Last In First Out) ordering",
                "Stores local variables and return addresses",
                "Enables nested function calls",
            ],
            "max_score": 1.0,
        },
        "expected_good_answer": "The call stack is a LIFO data structure that keeps track of active function calls. Each function call pushes a new frame onto the stack containing local variables and return address. When a function completes, its frame is popped. Without a stack, we couldn't properly handle nested function calls or know where to return control.",
        "expected_weak_answer": "It's where functions are stored.",
    },
    "base-case": {
        "question_text": "Why does a recursive function need a base case? What happens if you forget it?",
        "question_type": "reasoning",
        "rubric": {
            "required_points": [
                "Stops the recursion",
                "Prevents infinite recursion",
                "Provides the simplest solution",
                "Stack overflow without it",
            ],
            "max_score": 1.0,
        },
        "expected_good_answer": "A base case is the terminating condition that stops recursion. Without it, the function would call itself infinitely, eventually causing a stack overflow error. The base case handles the simplest version of the problem that can be solved directly without recursion.",
        "expected_weak_answer": "To stop the function.",
    },
    "problem-decomposition": {
        "question_text": "Describe how you would break down the problem of calculating factorial(5) into smaller subproblems.",
        "question_type": "reasoning",
        "rubric": {
            "required_points": [
                "5! = 5 × 4!",
                "Each step is smaller",
                "Eventually reaches base case",
                "Pattern of reduction",
            ],
            "max_score": 1.0,
        },
        "expected_good_answer": "To calculate 5!, I need 5 × 4!. To get 4!, I need 4 × 3!. This continues: 3! = 3 × 2!, 2! = 2 × 1!, and 1! = 1 (base case). Each subproblem is simpler than the previous one.",
        "expected_weak_answer": "Calculate 5 times 4 times 3 times 2 times 1.",
    },
    "recursive-case": {
        "question_text": "In a recursive function, what should the recursive call do differently from the original call?",
        "question_type": "reasoning",
        "rubric": {
            "required_points": [
                "Work with a simpler/smaller input",
                "Move toward base case",
                "Return result that helps solve original",
                "Different state or parameters",
            ],
            "max_score": 1.0,
        },
        "expected_good_answer": "The recursive call should work with a simpler or smaller version of the problem, moving closer to the base case. For example, if processing a list, it might work with a shorter list. The result from the recursive call is then used to build the solution to the original problem.",
        "expected_weak_answer": "Call the function again.",
    },
    "state-transitions": {
        "question_text": "Trace what happens to the call stack when factorial(3) executes recursively.",
        "question_type": "reasoning",
        "rubric": {
            "required_points": [
                "factorial(3) calls factorial(2)",
                "factorial(2) calls factorial(1)",
                "factorial(1) returns 1",
                "Values multiply on the way back up",
                "Stack grows then shrinks",
            ],
            "max_score": 1.0,
        },
        "expected_good_answer": "factorial(3) pushes onto stack, calls factorial(2). That pushes and calls factorial(1). factorial(1) returns 1 (base case). factorial(2) pops, receives 1, returns 2×1=2. factorial(3) pops, receives 2, returns 3×2=6. Stack grows to depth 3 then shrinks back to 0.",
        "expected_weak_answer": "The function calls itself 3 times.",
    },
}

# Socratic tutoring dialogue for "call-stack" (identified as root gap)
TUTORING_DIALOGUE = [
    {
        "role": "assistant",
        "content": "Let's explore the call stack together. Imagine you have three boxes that you can only stack on top of each other. If you want to get to the bottom box, what do you need to do first?",
        "hint_level": 1,
    },
    {
        "role": "user",
        "content": "Remove the top boxes first?",
    },
    {
        "role": "assistant",
        "content": "Exactly! You need to remove them in the opposite order you added them. This is called LIFO - Last In, First Out. Now, how do you think this relates to function calls?",
        "hint_level": 1,
    },
    {
        "role": "user",
        "content": "When a function calls another function, it needs to wait for that function to finish?",
    },
    {
        "role": "assistant",
        "content": "Great insight! Yes, when function A calls function B, function A pauses and waits. The call stack keeps track of this. Let me give you a concrete example:\n\n```python\ndef first():\n    print('Start first')\n    second()\n    print('End first')\n\ndef second():\n    print('In second')\n```\n\nWhat do you think the call stack looks like when we're inside `second()`?",
        "hint_level": 2,
    },
    {
        "role": "user",
        "content": "Both first and second are on the stack?",
    },
    {
        "role": "assistant",
        "content": "Perfect! The stack has `first()` on bottom and `second()` on top. Each function's frame stores its local variables and where to return. When `second()` finishes, its frame is popped off, and `first()` resumes at the line after the function call. This is exactly how recursion works - recursive calls stack up, then unwind one by one. Does this help clarify how the call stack manages function execution?",
        "hint_level": 2,
    },
]

# Teach-back example
TEACHBACK_EXAMPLE = {
    "student_explanation": "The call stack is a LIFO data structure that keeps track of function calls. When you call a function, a new frame is pushed onto the stack with the function's local variables and return address. When the function finishes, the frame is popped off and control returns to the previous function. This is important for recursion because each recursive call adds a new frame to the stack, and they all get resolved in reverse order as the base case is reached and the calls return.",
    "coverage_score": 0.92,
    "reasoning_score": 0.88,
    "clarity_score": 0.90,
    "misconceptions": [],
    "missing_points": ["Could mention stack overflow risk"],
}


async def get_or_create_demo_user(db: AsyncSession) -> User:
    """Get existing demo user or create new one."""
    result = await db.execute(
        select(User).where(User.email == DEMO_USER_EMAIL)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        user = User(
            email=DEMO_USER_EMAIL,
            name=DEMO_USER_NAME,
        )
        db.add(user)
        await db.flush()
        print(f"✓ Created demo user: {DEMO_USER_EMAIL}")
    else:
        print(f"✓ Found existing demo user: {DEMO_USER_EMAIL}")
    
    return user


async def create_demo_session(db: AsyncSession, user: User) -> LearningSession:
    """Create a demo learning session with all data."""
    # Check if demo session already exists
    result = await db.execute(
        select(LearningSession)
        .where(LearningSession.user_id == user.id)
        .where(LearningSession.original_prompt == "I don't understand recursion")
    )
    existing_session = result.scalar_one_or_none()
    
    if existing_session:
        print(f"✓ Demo session already exists (id: {existing_session.id})")
        return existing_session
    
    # Create new session
    session = LearningSession(
        user_id=user.id,
        original_prompt="I don't understand recursion",
        normalized_topic="Recursion in Programming",
        status="diagnosing",  # Start in diagnosing state for demo
    )
    db.add(session)
    await db.flush()
    print(f"✓ Created demo session: {session.id}")
    
    # Create concepts
    concepts_by_slug = {}
    
    # Create target concept first
    target_concept = Concept(
        session_id=session.id,
        slug=RECURSION_GRAPH["target"]["slug"],
        name=RECURSION_GRAPH["target"]["name"],
        description=RECURSION_GRAPH["target"]["description"],
        is_target=True,
        mastery_score=Decimal("0.15"),
        confidence_score=Decimal("0.35"),
        status="weak",
    )
    db.add(target_concept)
    await db.flush()
    concepts_by_slug[target_concept.slug] = target_concept
    print(f"  ✓ Created target concept: {target_concept.name}")
    
    # Update session target_concept_id
    session.target_concept_id = target_concept.id
    
    # Create prerequisite concepts with varied mastery levels
    mastery_levels = {
        "function-calls": (Decimal("0.75"), Decimal("0.80"), "understood"),
        "call-stack": (Decimal("0.28"), Decimal("0.80"), "weak"),  # Root gap
        "base-case": (Decimal("0.45"), Decimal("0.60"), "learning"),
        "recursive-case": (Decimal("0.20"), Decimal("0.35"), "weak"),
        "problem-decomposition": (Decimal("0.52"), Decimal("0.60"), "learning"),
        "state-transitions": (Decimal("0.35"), Decimal("0.35"), "weak"),
    }
    
    for concept_data in RECURSION_GRAPH["concepts"]:
        mastery, confidence, status = mastery_levels[concept_data["slug"]]
        concept = Concept(
            session_id=session.id,
            slug=concept_data["slug"],
            name=concept_data["name"],
            description=concept_data["description"],
            is_target=False,
            mastery_score=mastery,
            confidence_score=confidence,
            status=status,
        )
        db.add(concept)
        await db.flush()
        concepts_by_slug[concept.slug] = concept
        print(f"  ✓ Created concept: {concept.name} (mastery: {mastery}, confidence: {confidence})")
    
    # Create edges
    for edge_data in RECURSION_GRAPH["edges"]:
        source = concepts_by_slug[edge_data["source"]]
        target = concepts_by_slug[edge_data["target"]]
        edge = ConceptEdge(
            session_id=session.id,
            source_concept_id=source.id,
            target_concept_id=target.id,
            importance_weight=Decimal(str(edge_data["weight"])),
        )
        db.add(edge)
    
    await db.flush()
    print(f"  ✓ Created {len(RECURSION_GRAPH['edges'])} prerequisite edges")
    
    # Create diagnostic questions and attempts
    for slug, question_data in DIAGNOSTIC_QUESTIONS.items():
        concept = concepts_by_slug[slug]
        
        question = DiagnosticQuestion(
            session_id=session.id,
            concept_id=concept.id,
            question_text=question_data["question_text"],
            question_type=question_data["question_type"],
            rubric_json=question_data["rubric"],
            difficulty=Decimal("0.5"),
        )
        db.add(question)
        await db.flush()
        
        # Create an attempt with realistic scores based on concept mastery
        mastery_val = float(concept.mastery_score)
        attempt = DiagnosticAttempt(
            question_id=question.id,
            session_id=session.id,
            concept_id=concept.id,
            student_answer=question_data.get("expected_good_answer", "Student answer here"),
            correctness_score=Decimal(str(mastery_val)),
            reasoning_score=Decimal(str(max(0.0, mastery_val - 0.1))),
        )
        db.add(attempt)
        
        # Create mastery event for this diagnostic
        mastery_event = MasteryEvent(
            session_id=session.id,
            concept_id=concept.id,
            source_type="diagnostic",
            old_score=Decimal("0.0"),
            new_score=concept.mastery_score,
            old_confidence=Decimal("0.1"),
            new_confidence=concept.confidence_score,
            reason_json={
                "action": "diagnostic_completed",
                "question_id": str(question.id),
                "correctness_score": float(attempt.correctness_score),
                "reasoning_score": float(attempt.reasoning_score),
            },
        )
        db.add(mastery_event)
    
    await db.flush()
    print(f"  ✓ Created {len(DIAGNOSTIC_QUESTIONS)} diagnostic questions with attempts")
    
    # Create tutoring dialogue for call-stack (the root gap)
    call_stack_concept = concepts_by_slug["call-stack"]
    for msg_data in TUTORING_DIALOGUE:
        message = TutorMessage(
            session_id=session.id,
            concept_id=call_stack_concept.id,
            role=msg_data["role"],
            content=msg_data["content"],
            hint_level=msg_data.get("hint_level"),
        )
        db.add(message)
    
    await db.flush()
    print(f"  ✓ Created {len(TUTORING_DIALOGUE)} tutoring messages for call-stack")
    
    # Create teach-back attempt for call-stack
    teachback = TeachBackAttempt(
        session_id=session.id,
        concept_id=call_stack_concept.id,
        student_explanation=TEACHBACK_EXAMPLE["student_explanation"],
        coverage_score=Decimal(str(TEACHBACK_EXAMPLE["coverage_score"])),
        reasoning_score=Decimal(str(TEACHBACK_EXAMPLE["reasoning_score"])),
        clarity_score=Decimal(str(TEACHBACK_EXAMPLE["clarity_score"])),
        misconceptions_json={"misconceptions": TEACHBACK_EXAMPLE["misconceptions"]},
        missing_points_json={"missing": TEACHBACK_EXAMPLE["missing_points"]},
    )
    db.add(teachback)
    await db.flush()
    print(f"  ✓ Created teach-back attempt for call-stack")
    
    # Update call-stack mastery after successful teach-back
    new_mastery = Decimal("0.78")
    new_confidence = Decimal("0.85")
    mastery_event = MasteryEvent(
        session_id=session.id,
        concept_id=call_stack_concept.id,
        source_type="teachback",
        old_score=call_stack_concept.mastery_score,
        new_score=new_mastery,
        old_confidence=call_stack_concept.confidence_score,
        new_confidence=new_confidence,
        reason_json={
            "action": "teachback_completed",
            "teachback_id": str(teachback.id),
            "avg_score": float((
                TEACHBACK_EXAMPLE["coverage_score"] +
                TEACHBACK_EXAMPLE["reasoning_score"] +
                TEACHBACK_EXAMPLE["clarity_score"]
            ) / 3),
        },
    )
    db.add(mastery_event)
    
    call_stack_concept.mastery_score = new_mastery
    call_stack_concept.confidence_score = new_confidence
    call_stack_concept.status = "understood"
    
    await db.flush()
    print(f"  ✓ Updated call-stack mastery to {new_mastery} after teach-back")
    
    await db.commit()
    print(f"\n✓ Demo session created successfully!")
    print(f"  Session ID: {session.id}")
    print(f"  User: {user.email}")
    print(f"  Concepts: {len(concepts_by_slug)}")
    print(f"  Target: {target_concept.name}")
    print(f"  Root gap (was): call-stack (now resolved)")
    
    return session


async def main():
    """Seed demo data."""
    print("=" * 60)
    print("RootLearn Demo Data Seeder")
    print("=" * 60)
    print()
    
    async with AsyncSessionLocal() as db:
        try:
            # Create demo user
            user = await get_or_create_demo_user(db)
            
            # Create demo session with full data
            session = await create_demo_session(db, user)
            
            print()
            print("=" * 60)
            print("Demo data seeded successfully!")
            print("=" * 60)
            print()
            print(f"Demo user email: {DEMO_USER_EMAIL}")
            print(f"Session ID: {session.id}")
            print(f"Status: {session.status}")
            print()
            print("You can now use this session for demos and presentations.")
            print("The session shows a realistic learning journey through recursion.")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
