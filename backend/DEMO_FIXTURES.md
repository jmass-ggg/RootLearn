# RootLearn Demo Fixtures

This document describes the pre-built demo scenario for presentations and testing.

## Overview

The demo fixture creates a complete learning session for the prompt **"I don't understand recursion"**. This scenario demonstrates all major features of RootLearn:

- ✓ Prerequisite graph generation
- ✓ Diagnostic assessment
- ✓ Root gap detection
- ✓ Socratic tutoring
- ✓ Teach-back verification
- ✓ Mastery tracking

## Running the Demo Seed Script

```bash
cd backend
python seed_demo.py
```

The script is **idempotent** - running it multiple times will not create duplicate data.

## Demo User

- **Email**: `demo@rootlearn.example`
- **Name**: Demo User
- **Password**: None (authentication not implemented in MVP)

## Recursion Learning Scenario

### Target Concept

**Recursion**: A programming technique where a function calls itself to solve smaller instances of the same problem.

### Prerequisite Graph

The graph contains 7 concepts total (including the target):

```
                    ┌─────────────────────┐
                    │   Function Calls    │
                    │   (mastery: 0.75)   │
                    └──────────┬──────────┘
                               │ 0.9
                               ▼
                    ┌─────────────────────┐
                    │    Call Stack       │
                    │   (mastery: 0.78)   │  ← Root gap (resolved)
                    └──────────┬──────────┘
                               │ 0.95
                               ▼
    ┌──────────────────┐    ┌─────────────────────┐    ┌──────────────────┐
    │   Base Case      │───▶│     Recursion       │◀───│ Recursive Case   │
    │ (mastery: 0.45)  │0.9 │   (mastery: 0.15)   │0.9 │ (mastery: 0.20)  │
    └──────────────────┘    └─────────────────────┘    └──────────────────┘
                                       ▲
                                       │ 0.85
                            ┌──────────┴──────────┐
                            │ Problem             │
                            │ Decomposition       │
                            │ (mastery: 0.52)     │
                            └─────────────────────┘
                                       ▲
                                       │ 0.75
                            ┌──────────┴──────────┐
                            │ State Transitions   │
                            │ (mastery: 0.35)     │
                            └─────────────────────┘
```

### Mastery Levels

| Concept | Mastery | Confidence | Status | Notes |
|---------|---------|------------|--------|-------|
| Recursion | 0.15 | 0.35 | weak | Target concept |
| Function Calls | 0.75 | 0.80 | understood | Strong foundation |
| Call Stack | 0.78 | 0.85 | understood | **Was root gap, now resolved** |
| Base Case | 0.45 | 0.60 | learning | Partial understanding |
| Recursive Case | 0.20 | 0.35 | weak | Weak, but depends on call stack |
| Problem Decomposition | 0.52 | 0.60 | learning | Moderate understanding |
| State Transitions | 0.35 | 0.35 | weak | Early understanding |

### Diagnostic Questions

The demo includes 6 diagnostic questions, one for each prerequisite concept:

1. **Function Calls**: "Explain what happens when you call a function in Python. What information needs to be tracked?"
2. **Call Stack**: "What is the call stack and why is it important? What would happen if functions didn't use a stack?"
3. **Base Case**: "Why does a recursive function need a base case? What happens if you forget it?"
4. **Problem Decomposition**: "Describe how you would break down the problem of calculating factorial(5) into smaller subproblems."
5. **Recursive Case**: "In a recursive function, what should the recursive call do differently from the original call?"
6. **State Transitions**: "Trace what happens to the call stack when factorial(3) executes recursively."

Each question includes:
- Question text
- Question type (reasoning, short_answer, etc.)
- Detailed rubric with required points
- Example good answer
- Example weak answer

### Tutoring Dialogue

A complete Socratic tutoring conversation for the **Call Stack** concept (identified as the root gap):

**Turn 1 (Assistant, Hint Level 1)**:
> Let's explore the call stack together. Imagine you have three boxes that you can only stack on top of each other. If you want to get to the bottom box, what do you need to do first?

**Turn 2 (Student)**:
> Remove the top boxes first?

**Turn 3 (Assistant, Hint Level 1)**:
> Exactly! You need to remove them in the opposite order you added them. This is called LIFO - Last In, First Out. Now, how do you think this relates to function calls?

**Turn 4 (Student)**:
> When a function calls another function, it needs to wait for that function to finish?

**Turn 5 (Assistant, Hint Level 2)**:
> Great insight! Yes, when function A calls function B, function A pauses and waits. The call stack keeps track of this. Let me give you a concrete example:
>
> ```python
> def first():
>     print('Start first')
>     second()
>     print('End first')
> 
> def second():
>     print('In second')
> ```
>
> What do you think the call stack looks like when we're inside `second()`?

**Turn 6 (Student)**:
> Both first and second are on the stack?

**Turn 7 (Assistant, Hint Level 2)**:
> Perfect! The stack has `first()` on bottom and `second()` on top. Each function's frame stores its local variables and where to return. When `second()` finishes, its frame is popped off, and `first()` resumes at the line after the function call. This is exactly how recursion works - recursive calls stack up, then unwind one by one. Does this help clarify how the call stack manages function execution?

### Teach-Back Example

After tutoring, the student provides this teach-back explanation:

> The call stack is a LIFO data structure that keeps track of function calls. When you call a function, a new frame is pushed onto the stack with the function's local variables and return address. When the function finishes, the frame is popped off and control returns to the previous function. This is important for recursion because each recursive call adds a new frame to the stack, and they all get resolved in reverse order as the base case is reached and the calls return.

**Evaluation Scores**:
- Coverage: 0.92
- Reasoning: 0.88
- Clarity: 0.90
- Average: 0.90 (sufficient for mastery update)

**Missing Points**: Could mention stack overflow risk

After this successful teach-back, the Call Stack concept's mastery increases from 0.28 to 0.78, moving from "weak" to "understood".

### Learning Journey Flow

The demo session demonstrates this realistic learning flow:

1. **Initial State**: Student starts with "I don't understand recursion"
2. **Target Identification**: System identifies "Recursion" as target concept
3. **Graph Generation**: Creates prerequisite graph with 6 prerequisites
4. **Diagnostic Phase**: Asks 6 diagnostic questions to assess understanding
5. **Root Gap Detection**: Identifies "Call Stack" as the weakest high-impact gap
   - Gap score calculation: (1 - 0.28) × 0.80 × 0.95 × 2.0 = 1.094
6. **Tutoring Phase**: Provides Socratic guidance on call stack concept
7. **Teach-Back**: Student explains call stack in their own words
8. **Mastery Update**: Call stack mastery increases to 0.78 (understood)
9. **Next Steps**: System would recommend next weak concept (Recursive Case or State Transitions)

## Using the Demo Data

### For Presentations

1. Run the seed script to create demo data
2. Start the backend server
3. Use the demo session ID in API calls
4. Show the complete learning journey

### For Testing

The demo data provides:
- Realistic graph structure for testing graph algorithms
- Varied mastery levels for testing mastery calculations
- Complete tutoring dialogue for testing UI components
- Example questions and answers for validation

### For Development

Reference the demo data structure when:
- Building new features
- Testing edge cases
- Validating UI layouts
- Debugging issues

## Data Integrity

All demo data follows the same validation rules as production data:

- ✓ Mastery scores in [0, 1]
- ✓ Confidence scores in [0, 1]
- ✓ Valid concept status values
- ✓ DAG structure (no cycles)
- ✓ Proper foreign key relationships
- ✓ Appropriate cascade rules

## Cleanup

To remove demo data:

```sql
-- Delete demo user and all associated data (cascades)
DELETE FROM users WHERE email = 'demo@rootlearn.example';
```

Or use the Python shell:

```python
from app.database import AsyncSessionLocal
from app.models import User
from sqlalchemy import select

async with AsyncSessionLocal() as db:
    result = await db.execute(
        select(User).where(User.email == "demo@rootlearn.example")
    )
    user = result.scalar_one_or_none()
    if user:
        await db.delete(user)
        await db.commit()
        print("Demo user and all data deleted")
```

## Future Enhancements

Potential additions to demo fixtures:

- Multiple demo scenarios (different subjects)
- Different starting mastery levels
- Edge cases (very weak, very strong initial state)
- Different graph structures (deep vs wide)
- Failed teach-back examples
- Multiple attempts on same concept

## Questions?

For questions about the demo data structure, see:
- `backend/seed_demo.py` - Full implementation
- `backend/app/models.py` - Database schema
- `.kiro/specs/rootlearn-knowledge-debugger/design.md` - System design
