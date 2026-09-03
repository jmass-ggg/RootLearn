# Hard-Coded Data Audit

**Date**: December 2024  
**Feature**: RootLearn UI/UX Redesign  
**Task**: 14.4 - Avoid hard-coded screenshot data  
**Requirements**: 12.9

## Executive Summary

This audit verifies that no hard-coded screenshot-specific data (names, IDs, scores, concepts) has been introduced in the redesigned UI. All dynamic content comes from API responses or intentional placeholder/example data for UX purposes.

## Audit Methodology

### Search Patterns
1. Hard-coded concept names in production code
2. Hard-coded session IDs
3. Hard-coded concept IDs
4. Hard-coded mastery scores
5. Hard-coded confidence values
6. Hard-coded user names
7. Hard-coded evaluation results

### Exclusions
- Test files (`**/__tests__/**`) - Expected to have mock data
- Placeholder text for empty states - Acceptable
- Example prompts for UX - Acceptable
- Topic suggestions for quick start - Intentional UX feature

## Findings

### 1. Topic Suggestions (Acceptable)

**Location**: 
- `frontend/src/app/page.tsx`
- `frontend/src/app/new-session/page.tsx`

**Code**:
```typescript
const suggestedTopics = ["Recursion", "Calculus", "Probability", "SQL Joins", "Neural Networks"];
```

**Assessment**: ✅ **Acceptable**
- **Reason**: Intentional UX feature to help users get started quickly
- **Not from screenshots**: These are universal example topics
- **User can override**: User can type any topic they want
- **No backend coupling**: Not tied to any specific backend data

### 2. Example Prompts (Acceptable)

**Location**:
- `frontend/src/app/page.tsx`
- `frontend/src/app/new-session/page.tsx`

**Code**:
```typescript
placeholder="I understand loops, but recursion still confuses me..."
```

**Assessment**: ✅ **Acceptable**
- **Reason**: Demonstrates expected input format to users
- **Standard UX pattern**: Common practice for text inputs
- **Not tied to data**: Purely for user guidance

### 3. Session ID Empty Strings (Acceptable)

**Location**: `frontend/src/app/new-session/page.tsx`

**Code**:
```typescript
<SessionShell
  sessionId=""
  userId=""
  currentPhase="analyzing"
  topic="New Session"
>
```

**Assessment**: ✅ **Acceptable**
- **Reason**: Placeholder for new session page (no session exists yet)
- **Documented**: Component comment explains this is expected
- **No API calls**: Page doesn't make API calls with these empty values

## Dynamic Data Verification

### All Content Sources from API

#### Session Data
```typescript
✅ session.id - from GET /sessions/{id}
✅ session.user_id - from session creation response
✅ session.original_prompt - from API
✅ session.normalized_topic - from API
✅ session.target_concept_id - from API
✅ session.status - from API
```

**Verification**: All session fields displayed come from API responses ✅

#### Graph Data
```typescript
✅ graph.concepts - from GET /sessions/{id}/graph
  ✅ concept.id - from API
  ✅ concept.name - from API
  ✅ concept.description - from API
  ✅ concept.mastery_score - from API
  ✅ concept.confidence_score - from API
  ✅ concept.status - from API
  ✅ concept.is_target - from API
  ✅ concept.is_root_gap - from API
✅ graph.edges - from API
  ✅ edge.source_id - from API
  ✅ edge.target_id - from API
  ✅ edge.importance_weight - from API
```

**Verification**: All graph data displayed comes from API responses ✅

#### Diagnostic Data
```typescript
✅ currentQuestion.question_id - from GET /sessions/{id}/diagnosis/current
✅ currentQuestion.question_text - from API
✅ currentQuestion.concept_id - from API
✅ currentQuestion.concept_name - from API
✅ lastEvaluation.correctness_score - from POST /sessions/{id}/diagnosis/answer
✅ lastEvaluation.reasoning_score - from API
✅ lastEvaluation.demonstrated_knowledge - from API
✅ lastEvaluation.missing_knowledge - from API
✅ lastEvaluation.misconceptions - from API
```

**Verification**: All diagnostic content comes from API responses ✅

#### Root Gap Data
```typescript
✅ rootGap.root_gap.concept_id - from GET /sessions/{id}/root-gap
✅ rootGap.root_gap.concept_name - from API
✅ rootGap.root_gap.mastery_score - from API
✅ rootGap.root_gap.confidence_score - from API
✅ rootGap.root_gap.gap_score - from API
✅ rootGap.root_gap.message - from API
✅ rootGap.root_gap.reasons - from API (array)
```

**Verification**: All root gap content comes from API responses ✅

#### Tutor Data
```typescript
✅ tutorData.concept_id - from GET /sessions/{id}/tutor/messages
✅ tutorData.concept_name - from API
✅ tutorData.messages - from API (array)
  ✅ message.role - from API
  ✅ message.content - from API
  ✅ message.timestamp - from API
✅ Current concept mastery - from graph.concepts.find(...)
✅ Current concept confidence - from graph.concepts.find(...)
```

**Verification**: All tutor content comes from API responses ✅

#### Teach-Back Data
```typescript
✅ currentConcept - derived from tutorData
✅ teachBackEvaluation.coverage_score - from POST /sessions/{id}/teachback
✅ teachBackEvaluation.reasoning_score - from API
✅ teachBackEvaluation.clarity_score - from API
✅ teachBackEvaluation.strengths - from API (array)
✅ teachBackEvaluation.gaps - from API (array)
✅ teachBackEvaluation.pass_threshold - from API
```

**Verification**: All teach-back content comes from API responses ✅

#### Mastery Events Data
```typescript
✅ masteryEvents - from GET /sessions/{id}/mastery-events
  ✅ event.concept_id - from API
  ✅ event.concept_name - from API
  ✅ event.old_score - from API
  ✅ event.new_score - from API
  ✅ event.old_confidence - from API
  ✅ event.new_confidence - from API
  ✅ event.change_reason - from API
```

**Verification**: All mastery tracking comes from API responses ✅

## Component Analysis

### Components Using Only API Data

#### ✅ KnowledgeGraph
- **Props**: `concepts`, `edges`, `targetId`, `rootGapId`
- **All from API**: Yes
- **No hard-coded data**: Confirmed

#### ✅ DiagnosticAssessmentCard
- **Props**: `question`, `evaluation`, `isLoading`, `onSubmitAnswer`
- **All from API**: Yes
- **No hard-coded data**: Confirmed

#### ✅ RootGapCard
- **Props**: `rootGap`, `isLoading`, `onFixGap`
- **All from API**: Yes
- **No hard-coded data**: Confirmed

#### ✅ TutorPanel
- **Props**: `sessionId`, `userId`, `messages`, `currentConcept`, `masteryScore`, `confidenceScore`
- **All from API or derived from API**: Yes
- **No hard-coded data**: Confirmed

#### ✅ TeachBackPanel
- **Props**: `currentConcept`, `masteryScore`, `confidenceScore`, `evaluation`, `isLoading`
- **All from API or derived from API**: Yes
- **No hard-coded data**: Confirmed

#### ✅ KnowledgeMapCard
- **Props**: `graph`, `isLoading`, `error`, `topic`, `onRetry`
- **All from API**: Yes
- **No hard-coded data**: Confirmed

### Components with Intentional Static Content

#### SessionShell / AppShell
- **Static Content**: Sidebar section labels, phase names
- **Reason**: UI chrome, not data content
- **Acceptable**: ✅ Yes

#### Button, Card, StateDisplay
- **Static Content**: None (pure UI components)
- **Data Content**: None
- **Acceptable**: ✅ Yes

## Empty State Messages

All empty/error state messages are generic and not tied to specific data:

### Loading States
```typescript
✅ "Loading your learning session..."
✅ "Loading..."
✅ "Analyzing your topic"
```
**Assessment**: Generic, not screenshot-specific ✅

### Empty States
```typescript
✅ "No concepts to display"
✅ "No messages yet"
✅ "No root gap found"
```
**Assessment**: Generic, honest messaging ✅

### Error States
```typescript
✅ "Failed to load session"
✅ "Missing User ID"
✅ "Session Not Found"
✅ "An error occurred"
```
**Assessment**: Generic error messages, not data-specific ✅

## Defensive Rendering Verification

All components handle undefined/null data properly without defaulting to hard-coded values:

### Example: Graph Component
```typescript
if (concepts === undefined || edges === undefined) {
  return <LoadingState />;
}

if (concepts.length === 0) {
  return <EmptyState message="No concepts to display" />;
}

// Render actual data
return <ReactFlow nodes={concepts.map(...)} edges={edges.map(...)} />;
```

✅ **Verified**: No hard-coded fallback data, only states

### Example: Diagnostic Component
```typescript
if (!question) {
  return <EmptyState message="No question available" />;
}

// Render actual question
return <Card>{question.question_text}</Card>;
```

✅ **Verified**: Uses actual API data or shows honest empty state

## Test Data (Excluded from Audit)

Test files contain mock data, which is expected and acceptable:
- `frontend/src/components/__tests__/DiagnosticPanel.test.tsx`
- `frontend/src/components/__tests__/RootGapCard.test.tsx`
- `frontend/src/components/__tests__/KnowledgeGraph.test.tsx`
- `frontend/src/components/__tests__/TeachBackPanel.test.tsx`

**Assessment**: ✅ Test data is appropriate and necessary

## Screenshot Comparison

### Reference Screenshots Analysis

Based on the requirements and design document, reference screenshots showed:
- Navy backgrounds ✅ Implemented with design tokens
- Lime accents ✅ Implemented with design tokens
- Card layouts ✅ Implemented with reusable components
- Knowledge graphs ✅ Implemented with dynamic data
- Example topics ✅ Implemented as UX suggestions (intentional)

**Key Finding**: No screenshot-specific user data, session data, or concept data has been hard-coded. All actual content is API-driven.

## Placeholder vs. Hard-Coded Data

### Acceptable Placeholders
These are intentional UX patterns, not screenshot data:
- ✅ Topic suggestions for quick start
- ✅ Example prompts showing input format
- ✅ Generic empty state messages
- ✅ Loading state messages

### Would Be Unacceptable (None Found)
Examples of what we would flag:
- ❌ Hard-coded session IDs like "abc-123-def"
- ❌ Hard-coded concept names in display logic
- ❌ Hard-coded mastery scores like 0.85
- ❌ Hard-coded user names like "John Doe"
- ❌ Hard-coded evaluation messages
- ❌ Screenshot-specific data in production code

**Result**: ✅ **None of these antipatterns found**

## Dynamic Content Checklist

| Content Type | Source | Status |
|--------------|--------|--------|
| Session ID | URL params / API | ✅ Dynamic |
| User ID | URL params / API | ✅ Dynamic |
| Session status | API response | ✅ Dynamic |
| Topic/prompt | API response | ✅ Dynamic |
| Concept names | API response | ✅ Dynamic |
| Concept IDs | API response | ✅ Dynamic |
| Mastery scores | API response | ✅ Dynamic |
| Confidence scores | API response | ✅ Dynamic |
| Question text | API response | ✅ Dynamic |
| Evaluation results | API response | ✅ Dynamic |
| Tutor messages | API response | ✅ Dynamic |
| Root gap data | API response | ✅ Dynamic |
| Teach-back evaluation | API response | ✅ Dynamic |
| Mastery events | API response | ✅ Dynamic |
| Graph structure | API response | ✅ Dynamic |
| Edge connections | API response | ✅ Dynamic |

## Code Review Checklist

Verified all production code for:
- ✅ No hard-coded session IDs
- ✅ No hard-coded user IDs or names
- ✅ No hard-coded concept IDs
- ✅ No hard-coded concept names in logic
- ✅ No hard-coded scores or percentages
- ✅ No hard-coded evaluation messages
- ✅ No hard-coded graph structures
- ✅ No screenshot-specific data anywhere

## Compliance Summary

| Requirement | Status | Notes |
|-------------|--------|-------|
| 12.9 - No hard-coded names | ✅ Pass | All names from API |
| 12.9 - No hard-coded IDs | ✅ Pass | All IDs from API |
| 12.9 - No hard-coded scores | ✅ Pass | All scores from API |
| 12.9 - No hard-coded concepts | ✅ Pass | All concepts from API |
| 12.9 - Dynamic content from API | ✅ Pass | All content is API-driven |

## Recommendations

### Maintain This Standard
1. **Code Review Practice**: Check all new components for hard-coded data
2. **Test with Real Data**: Always test with actual API responses
3. **Honest Placeholders**: Use generic messages for empty/error states
4. **Document Intentions**: Mark UX-intentional static content (like topic suggestions)

### Future Enhancements
1. **Topic Suggestions**: Could be moved to backend configuration
2. **Example Prompts**: Could be loaded from a content management system
3. **Empty Messages**: Could be internationalized for multi-language support

## Conclusion

**AUDIT RESULT: ✅ PASS**

No hard-coded screenshot-specific data has been introduced in the redesign. All dynamic content (names, IDs, scores, concepts, messages) comes from API responses. The only static content is intentional UX guidance (topic suggestions, example prompts) which is appropriate and documented.

The redesign successfully avoids the anti-pattern of replacing real application data with static screenshot data. Requirement 12.9 is fully satisfied.

### Key Achievements
- ✅ All session data is API-driven
- ✅ All graph data is API-driven
- ✅ All diagnostic content is API-driven
- ✅ All tutor messages are API-driven
- ✅ All evaluation results are API-driven
- ✅ Defensive rendering with honest empty/error states
- ✅ No screenshot artifacts in production code
