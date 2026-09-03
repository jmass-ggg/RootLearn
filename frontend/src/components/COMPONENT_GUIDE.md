# RootLearn Component Usage Guide

This guide provides patterns and best practices for using the RootLearn component library effectively.

## Table of Contents

- [Component Organization](#component-organization)
- [Layout Components](#layout-components)
- [UI Components](#ui-components)
- [Responsive Patterns](#responsive-patterns)
- [Common Combinations](#common-combinations)
- [Accessibility Guidelines](#accessibility-guidelines)

## Component Organization

```
src/components/
├── layout/          # Page structure components
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   └── SessionShell.tsx
├── ui/              # Reusable UI primitives
│   ├── Button.tsx
│   ├── Card.tsx
│   ├── StateDisplay.tsx
│   └── FadeTransition.tsx
└── [feature]/       # Feature-specific components
    ├── KnowledgeGraph.tsx
    ├── DiagnosticAssessmentCard.tsx
    ├── TutorPanel.tsx
    └── TeachBackPanel.tsx
```

### When to Create a New Component

**Create a new component when:**
- The pattern is used in 3+ places
- The component has clear, reusable props
- The styling is consistent across uses
- The behavior is self-contained

**Keep inline when:**
- The pattern is used only once or twice
- The styling varies significantly per use
- The component is tightly coupled to parent state

## Layout Components

### SessionShell

The main layout wrapper for all session screens. Provides header, optional sidebar, and workspace background.

**When to use:**
- All authenticated session screens
- Any screen that needs consistent navigation
- Screens where sidebar context is helpful

**When NOT to use:**
- Landing page (no active session)
- Standalone pages without session context

**Example:**
```tsx
import { SessionShell } from '@/components/layout/SessionShell';

export default function DiagnosticPage({ params }: { params: { sessionId: string } }) {
  const { data: session } = useSession(params.sessionId);
  
  return (
    <SessionShell
      sessionId={session.id}
      userId={session.user_id}
      currentPhase={session.status}
      topic={session.target_concept || session.prompt}
    >
      {/* Your page content */}
      <div className="max-w-7xl mx-auto">
        <DiagnosticContent />
      </div>
    </SessionShell>
  );
}
```

**Props guide:**
- `sessionId`: Pass empty string `""` if no active session
- `currentPhase`: Maps to sidebar highlighting
- `topic`: Show user's goal for context
- Always wrap actual content in a container with max-width

### Header

Top navigation bar with branding, session context, and actions.

**Used automatically by SessionShell** - you typically don't use this directly.

If you need to customize the header, use SessionShell's composition pattern or extend it.

### Sidebar

Left navigation panel showing workflow sections and current stage explanation.

**Used automatically by SessionShell** - you typically don't use this directly.

Sidebar visibility is controlled by SessionShell based on whether there's an active session.

## UI Components

### Button

Versatile action component with multiple variants and states.

**Variant selection guide:**

| Variant | Usage | Examples |
|---------|-------|----------|
| `primary` | Main action on screen | "Submit Answer", "Start Session" |
| `secondary` | Alternative action | "Cancel", "Skip" |
| `ghost` | Subtle tertiary action | "Edit", "View More" |
| `lime` | High-emphasis moment | "Start Guided Learning", Major CTAs |

**Size selection guide:**

| Size | Usage | Examples |
|------|-------|----------|
| `sm` | Compact UI elements | Inline actions, toolbar buttons |
| `md` | Default button size | Form submissions, standard actions |
| `lg` | Hero CTAs | Landing page primary action |

**Examples:**

```tsx
// Primary form submission
<Button 
  type="submit" 
  variant="primary"
  isDisabled={!isValid}
  isLoading={isSubmitting}
>
  Submit Answer
</Button>

// Secondary cancel action
<Button 
  variant="secondary"
  onClick={handleCancel}
>
  Cancel
</Button>

// High-emphasis moment (root gap discovery)
<Button 
  variant="lime"
  size="lg"
  onClick={handleStartTutoring}
>
  Start Guided Learning
</Button>

// Subtle inline action
<Button 
  variant="ghost"
  size="sm"
  onClick={handleViewDetails}
>
  View Details
</Button>
```

**Common mistakes to avoid:**
- ❌ Using lime variant for regular actions (reserve for special moments)
- ❌ Having multiple primary buttons on the same screen (use secondary for alternatives)
- ❌ Forgetting to disable during loading state
- ❌ Not setting appropriate type="submit" for form buttons

### Card

Container component for grouping related content.

**Variant selection guide:**

| Variant | Usage | Examples |
|---------|-------|----------|
| `default` | Standard content cards | Question display, form containers |
| `elevated` | Emphasized cards | Root gap result, important announcements |
| `navy` | High-contrast sections | Hero cards, celebration messages |

**Padding selection guide:**

| Padding | Usage | Examples |
|---------|-------|----------|
| `sm` | Tight spacing | List items, compact cards |
| `md` | Medium spacing | Form fields, inline content |
| `lg` | Standard (default) | Most content cards |
| `xl` | Spacious | Hero sections, major content areas |

**Examples:**

```tsx
// Standard content card
<Card>
  <h2 className="text-2xl font-semibold mb-4">Diagnostic Assessment</h2>
  <p className="text-text-body">Answer the following question...</p>
</Card>

// Elevated card for emphasis
<Card variant="elevated" padding="xl">
  <h2 className="text-3xl font-bold mb-2">Root Gap Found!</h2>
  <p className="text-xl">Functions and Variables</p>
</Card>

// Navy card for celebration
<Card variant="navy" className="text-center">
  <h1 className="text-4xl font-bold mb-4">Session Complete!</h1>
  <p className="text-xl text-text-inverse">Great work on mastering this concept.</p>
</Card>

// Compact card with custom padding
<Card padding="md" className="max-w-md">
  <div className="flex items-center gap-3">
    <Icon />
    <span>Compact content</span>
  </div>
</Card>
```

**Common mistakes to avoid:**
- ❌ Nesting cards inside cards (creates visual confusion)
- ❌ Using navy variant without considering text readability
- ❌ Overusing elevated variant (loses emphasis if everything is elevated)
- ❌ Forgetting to constrain card width on large screens

### StateDisplay

Centered feedback for loading, empty, and error states.

**When to use:**
- Data is still loading
- Data fetch returned empty results
- Operation failed with error
- Component is in transition state

**When NOT to use:**
- Inline form validation (use inline messages)
- Toast notifications (use toast library)
- Success confirmations (use success message in content area)

**Examples:**

```tsx
// Loading state while fetching
if (isLoading) {
  return (
    <StateDisplay
      variant="loading"
      title="Analyzing your understanding"
      description="This usually takes about a minute..."
    />
  );
}

// Error state with retry
if (error) {
  return (
    <StateDisplay
      variant="error"
      title="Failed to load session"
      description="There was a problem connecting to the server"
      action={{
        label: "Retry",
        onClick: () => refetch()
      }}
    />
  );
}

// Empty state with action
if (sessions.length === 0) {
  return (
    <StateDisplay
      variant="empty"
      title="No sessions yet"
      description="Start your first learning session to begin"
      action={{
        label: "Create Session",
        onClick: () => router.push('/new-session')
      }}
    />
  );
}

// Success - render actual content
return <SessionContent data={data} />;
```

**Message writing guide:**
- **Title**: Concise, descriptive (2-5 words)
- **Description**: Helpful context or next steps (1-2 sentences)
- **Action label**: Clear verb + noun ("Retry", "Create Session", "Go Back")

**Common mistakes to avoid:**
- ❌ Using StateDisplay for inline loading spinners (use small spinner component)
- ❌ Vague messages like "Something went wrong" (be specific when possible)
- ❌ Missing action button on empty states (guide user to next step)
- ❌ Action button on loading state (user should wait, not take action)

## Responsive Patterns

### Two-Column Desktop → Single Column Mobile

**Pattern:** Side-by-side layout on desktop, stacked layout on mobile.

**Breakpoints:**
- Mobile: < 768px (single column)
- Tablet: 768px - 1023px (single column or modified two-column)
- Desktop: ≥ 1024px (two-column)

**Example:**
```tsx
export default function DiagnosticScreen() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left: Knowledge Map */}
      <div className="lg:col-span-1">
        <KnowledgeMapCard />
      </div>
      
      {/* Right: Assessment */}
      <div className="lg:col-span-1">
        <DiagnosticAssessmentCard />
      </div>
    </div>
  );
}
```

### Compact Sidebar → Full Width Mobile

**Pattern:** Fixed sidebar on desktop, full-width stacked on mobile.

**Example:**
```tsx
export default function TutorScreen() {
  return (
    <div className="flex flex-col lg:flex-row gap-6">
      {/* Sidebar: Compact on desktop */}
      <div className="lg:w-64 flex-shrink-0">
        <TutorContextPanel />
      </div>
      
      {/* Main: Flexible width */}
      <div className="flex-1 min-w-0">
        <TutorConversationPanel />
      </div>
    </div>
  );
}
```

### Responsive Card Padding

**Pattern:** Reduce padding on mobile for better space usage.

**Example:**
```tsx
<Card 
  padding="lg"  // 24px on desktop
  className="p-4 lg:p-6"  // 16px mobile, 24px desktop
>
  <Content />
</Card>
```

### Responsive Typography

**Pattern:** Smaller text sizes on mobile, larger on desktop.

**Example:**
```tsx
<h1 className="text-2xl md:text-3xl lg:text-4xl font-bold">
  Find the gap behind the confusion
</h1>

<p className="text-sm md:text-base lg:text-lg">
  Supporting text scales with viewport
</p>
```

## Common Combinations

### Loading → Content → Error Pattern

Standard data fetching pattern with StateDisplay:

```tsx
export default function MyScreen() {
  const { data, isLoading, error, refetch } = useQuery(...);
  
  if (isLoading) {
    return (
      <StateDisplay
        variant="loading"
        title="Loading data"
      />
    );
  }
  
  if (error) {
    return (
      <StateDisplay
        variant="error"
        title="Failed to load"
        description={error.message}
        action={{ label: "Retry", onClick: () => refetch() }}
      />
    );
  }
  
  return <ActualContent data={data} />;
}
```

### Form with Button States

Standard form pattern with validation and loading:

```tsx
export default function SessionForm() {
  const [input, setInput] = useState('');
  const { mutate, isPending } = useMutation(...);
  
  const isValid = input.trim().length > 0;
  
  return (
    <Card>
      <form onSubmit={handleSubmit}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="w-full p-4 border rounded-lg"
        />
        
        <Button
          type="submit"
          variant="primary"
          isDisabled={!isValid}
          isLoading={isPending}
        >
          {isPending ? 'Creating...' : 'Create Session'}
        </Button>
      </form>
    </Card>
  );
}
```

### Card with Header and Actions

Content card with title and action buttons:

```tsx
<Card>
  {/* Header with title and action */}
  <div className="flex items-center justify-between mb-6">
    <h2 className="text-2xl font-semibold">Session Details</h2>
    <Button variant="ghost" size="sm" onClick={handleEdit}>
      Edit
    </Button>
  </div>
  
  {/* Content */}
  <div className="space-y-4">
    <p>Session information...</p>
  </div>
  
  {/* Footer actions */}
  <div className="flex gap-3 mt-6">
    <Button variant="primary" onClick={handleContinue}>
      Continue
    </Button>
    <Button variant="secondary" onClick={handleCancel}>
      Cancel
    </Button>
  </div>
</Card>
```

### Two-Column Layout with Responsive Behavior

Desktop two-column, mobile single-column:

```tsx
<SessionShell {...shellProps}>
  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
    {/* Left: 40% width on desktop */}
    <div className="lg:col-span-5">
      <Card>
        <LeftContent />
      </Card>
    </div>
    
    {/* Right: 60% width on desktop */}
    <div className="lg:col-span-7">
      <Card>
        <RightContent />
      </Card>
    </div>
  </div>
</SessionShell>
```

### Centered Hero with CTA

Landing page hero pattern:

```tsx
<div className="min-h-screen bg-brand-navy flex items-center justify-center px-4">
  <div className="max-w-4xl mx-auto text-center">
    <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-text-inverse mb-6">
      Find the gap behind the confusion
    </h1>
    
    <p className="text-lg md:text-xl text-text-inverse/80 mb-8">
      AI-powered prerequisite mapping to identify your root knowledge gaps
    </p>
    
    <Button variant="lime" size="lg" onClick={handleStart}>
      Start Learning
    </Button>
  </div>
</div>
```

### Progress Indicator with Steps

Multi-step progress display:

```tsx
<Card>
  <h2 className="text-2xl font-semibold mb-6">Analysis Progress</h2>
  
  <div className="space-y-4">
    {steps.map((step, index) => (
      <div key={step.id} className="flex items-center gap-3">
        {/* Status icon */}
        <div className="flex-shrink-0">
          {step.status === 'completed' && <CheckIcon />}
          {step.status === 'active' && <Spinner />}
          {step.status === 'pending' && <DotIcon />}
        </div>
        
        {/* Step text */}
        <span className={cn(
          "text-base",
          step.status === 'completed' && "text-mastery-mastered",
          step.status === 'active' && "text-brand-blue font-medium",
          step.status === 'pending' && "text-text-muted"
        )}>
          {step.label}
        </span>
      </div>
    ))}
  </div>
</Card>
```

## Accessibility Guidelines

### Keyboard Navigation

All interactive components should be keyboard accessible:

```tsx
// Good: Button is focusable and activatable with Enter/Space
<Button onClick={handleClick}>Click Me</Button>

// Good: Links work with Enter key
<a href="/session" className="text-brand-blue hover:underline">
  View Session
</a>

// Bad: Div with onClick requires manual keyboard handling
<div onClick={handleClick}>Clickable</div>  // ❌

// Better: Use button element
<button onClick={handleClick}>Clickable</button>  // ✅
```

### Focus States

All interactive elements have visible focus indicators (handled by components):

```tsx
// Components automatically include focus-visible:ring-2
<Button variant="primary">Focused Button</Button>

// Custom interactive elements need focus styles
<div
  tabIndex={0}
  className="cursor-pointer focus-visible:ring-2 focus-visible:ring-brand-blue focus-visible:ring-offset-2"
  onClick={handleClick}
>
  Custom Interactive Element
</div>
```

### ARIA Attributes

Use semantic HTML first, ARIA when needed:

```tsx
// Good: Semantic HTML (button)
<Button onClick={handleSubmit}>Submit</Button>

// Good: ARIA label for icon-only button
<Button aria-label="Close dialog" onClick={handleClose}>
  <XIcon />
</Button>

// Good: ARIA live region for dynamic updates
<StateDisplay variant="loading" title="Loading..." />
// (StateDisplay includes aria-live internally)

// Good: ARIA role for custom semantics
<Card role="article">
  <article>Article content</article>
</Card>
```

### Screen Reader Support

Provide text alternatives for non-text content:

```tsx
// Icon buttons need labels
<Button aria-label="Edit session" onClick={handleEdit}>
  <EditIcon aria-hidden="true" />
</Button>

// Status indicators need text
<div className="flex items-center gap-2">
  <div className="w-3 h-3 rounded-full bg-mastery-mastered" />
  <span>Mastered</span>  {/* Don't rely on color alone */}
</div>

// Loading states need announcements
<StateDisplay  // Includes aria-live="polite"
  variant="loading"
  title="Loading session data"
/>
```

### Color Contrast

Ensure sufficient contrast for text:

```tsx
// Good: High contrast combinations
<div className="bg-brand-navy text-text-inverse">
  Navy background with white text (14.4:1)
</div>

<Button variant="primary">
  Blue button with white text (8.2:1)
</Button>

// Check: Muted text on light background
<p className="text-text-muted bg-bg-workspace">
  Muted text (4.8:1) - meets WCAG AA
</p>

// Bad: Low contrast
<span className="text-text-muted text-opacity-50">
  Very light text  // ❌ Fails WCAG standards
</span>
```

## Best Practices Summary

### Component Selection

1. **Use SessionShell** for all authenticated session screens
2. **Use Card** for grouping related content
3. **Use Button** for all actions (avoid styled divs)
4. **Use StateDisplay** for loading/empty/error states

### Layout Patterns

1. **Start mobile-first**, then add desktop breakpoints
2. **Constrain content width** (`max-w-7xl mx-auto`) on large screens
3. **Use consistent spacing** from design tokens
4. **Test at multiple breakpoints** (375px, 768px, 1024px, 1440px)

### Styling

1. **Use Tailwind classes** for consistency
2. **Reference design tokens** when using custom styles
3. **Maintain hierarchy** with font sizes and weights
4. **Respect color semantics** (don't use mastery colors for other purposes)

### Accessibility

1. **Use semantic HTML** elements
2. **Provide text alternatives** for icons
3. **Ensure keyboard navigation** works
4. **Test color contrast** for WCAG AA compliance
5. **Include ARIA attributes** when semantic HTML isn't enough

### Performance

1. **Lazy load heavy components** (React Flow, large forms)
2. **Use React Query** for data fetching and caching
3. **Memoize expensive computations** with useMemo
4. **Optimize images** with next/image

## Getting Help

- **Design tokens**: See `src/theme/README.md`
- **Component props**: Check JSDoc comments in component files
- **Accessibility**: Review WCAG AA guidelines
- **Responsive design**: Test with browser dev tools

For questions or suggestions, consult with the team or refer to the design document in `.kiro/specs/rootlearn-ui-redesign/design.md`.
