# RootLearn Frontend

Next.js 15 frontend application for the RootLearn Knowledge Debugger.

## Prerequisites

- Node.js 20+
- npm or yarn

## Setup

### 1. Install Dependencies

```bash
npm install
```

Or using yarn:

```bash
yarn install
```

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` and configure the API URL:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start the Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Available Scripts

### Development

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
```

### Testing

```bash
npm run test         # Run unit tests with Vitest
npm run test:run     # Run unit tests once (no watch mode)
npm run test:e2e     # Run end-to-end tests with Playwright
npm run test:e2e:ui  # Run E2E tests with Playwright UI
npm run test:e2e:debug # Debug E2E tests
```

## Dependencies

### Why These Dependencies?

**Production Dependencies:**

1. **@tanstack/react-query (^5.17.0)**
   - **Purpose**: Server state management, data fetching, caching, and automatic polling
   - **Why necessary**: Handles session status polling during analysis phase, manages API cache invalidation after mutations, provides loading/error states automatically
   - **Alternative considered**: Native fetch + useState would require manual cache management and polling logic

2. **@xyflow/react (^12.0.0)**
   - **Purpose**: Interactive knowledge graph visualization
   - **Why necessary**: Core feature requirement - renders prerequisite concept relationships with pan, zoom, and node interaction
   - **Alternative considered**: Custom D3.js implementation would be significantly more complex

3. **next (^15.0.0)**
   - **Purpose**: React framework with App Router, server components, and optimizations
   - **Why necessary**: Project framework choice, provides routing, SSR, and build optimization

4. **react (^18.3.0) & react-dom (^18.3.0)**
   - **Purpose**: Core UI library
   - **Why necessary**: Required by Next.js and all React components

5. **uuid (^14.0.2)**
   - **Purpose**: Generate unique identifiers
   - **Why necessary**: Required for React Flow node IDs and session tracking
   - **Alternative considered**: Crypto.randomUUID() not available in all environments

6. **zod (^3.22.0)**
   - **Purpose**: Runtime type validation
   - **Why necessary**: Validates API responses at runtime to catch type mismatches from backend
   - **Alternative considered**: TypeScript only provides compile-time checking

**Development Dependencies:**

1. **@playwright/test (^1.62.1)**
   - **Purpose**: End-to-end testing framework
   - **Why necessary**: Tests complete user journeys across multiple screens (requirement 17.2)
   - **Alternative considered**: Cypress - Playwright has better TypeScript support

2. **@testing-library/react (^16.3.3) & @testing-library/jest-dom (^7.0.1)**
   - **Purpose**: Component testing utilities
   - **Why necessary**: Tests component behavior and user interactions (requirement 17.3)
   - **Alternative considered**: Enzyme - Testing Library better aligns with user behavior testing

3. **vitest (^4.1.11)**
   - **Purpose**: Fast unit test runner
   - **Why necessary**: TypeScript-first test runner, faster than Jest, better Next.js integration
   - **Alternative considered**: Jest - Vitest has native ESM and TypeScript support

4. **tailwindcss (^3.4.0)**
   - **Purpose**: Utility-first CSS framework
   - **Why necessary**: Implements design system tokens and enables rapid responsive styling
   - **Alternative considered**: CSS modules - Tailwind provides consistency and faster development

5. **typescript (^5.3.0)**
   - **Purpose**: Type-safe JavaScript
   - **Why necessary**: Catches errors at compile time, improves code maintainability (requirement 17.1)

**No new dependencies were added during the UI redesign.** All dependencies listed above were present before the redesign began. The redesign reused existing dependencies effectively:

- Used existing `@xyflow/react` for knowledge graph with improved defensive rendering
- Leveraged existing `@tanstack/react-query` for new screen polling and mutations
- Built design system using existing `tailwindcss` configuration
- Wrote tests using existing `vitest` and `@testing-library/react` setup

## Available Scripts

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── globals.css   # Global styles
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Home page
│   │   └── providers.tsx # React Query provider
│   ├── components/       # Reusable components
│   │   ├── layout/       # Page structure (Header, Sidebar, SessionShell)
│   │   ├── ui/           # UI primitives (Button, Card, StateDisplay)
│   │   └── [feature]/    # Feature-specific components
│   ├── lib/              # Shared utilities
│   │   └── api.ts        # API client
│   └── theme/            # Design system
│       ├── tokens.ts     # Design tokens (colors, spacing, typography)
│       └── README.md     # Design system documentation
├── public/               # Static assets
├── .env.local           # Environment variables (not in git)
├── .env.local.example   # Example environment file
├── next.config.js       # Next.js configuration
├── tailwind.config.ts   # Tailwind CSS configuration
├── tsconfig.json        # TypeScript configuration
└── package.json         # Dependencies
```

## Component Architecture

The RootLearn frontend uses a component-based architecture with three main layers:

### 1. Design System (`src/theme/`)

Core design tokens define the visual language:
- **Colors**: Brand colors (navy, blue, lime), semantic mastery colors, backgrounds
- **Spacing**: 4px-based scale for consistent layout
- **Typography**: Font sizes, weights, and hierarchy
- **Border Radius**: Consistent rounded corners

See `src/theme/README.md` for the complete design system guide.

### 2. Layout Components (`src/components/layout/`)

Reusable page structure components:

- **SessionShell**: Main layout wrapper for all session screens
  - Composes Header + Sidebar + workspace background
  - Highlights active section based on session phase
  - Handles responsive mobile navigation

- **Header**: Top navigation bar
  - Displays RootLearn branding, session context, phase badge
  - Provides "New session" action

- **Sidebar**: Left navigation panel
  - Shows workflow sections (Overview, Diagnosis, Tutor, etc.)
  - Highlights current phase
  - Displays contextual stage explanation

### 3. UI Primitives (`src/components/ui/`)

Reusable, composable UI components:

- **Button**: Action component with variants (primary, secondary, ghost, lime) and states (loading, disabled)
- **Card**: Container for grouping content with variants (default, elevated, navy)
- **StateDisplay**: Centered feedback for loading, empty, and error states
- **FadeTransition**: Smooth fade-in animation wrapper

### 4. Feature Components (`src/components/[feature]/`)

Feature-specific components built from primitives:

- **KnowledgeGraph**: Interactive React Flow graph with mastery state coloring
- **DiagnosticAssessmentCard**: Question display and answer submission
- **TutorPanel**: Socratic dialogue interface
- **TeachBackPanel**: Explanation submission and evaluation

### Component Guidelines

**When to use each:**

- **SessionShell**: All authenticated session screens
- **Card**: Grouping related content, forms, result displays
- **Button**: All user actions (forms, navigation, CTAs)
- **StateDisplay**: Loading states, empty results, error messages

**Best practices:**

1. Build feature components by composing UI primitives
2. Use design tokens from `src/theme/tokens.ts` for styling
3. Follow responsive patterns (mobile-first, desktop-enhanced)
4. Ensure keyboard accessibility and ARIA attributes
5. Handle loading, empty, and error states explicitly

See `src/components/COMPONENT_GUIDE.md` for detailed usage patterns and examples.

## Technology Stack

### Core

- **Next.js 15+**: React framework with App Router
- **React 18**: UI library
- **TypeScript**: Type-safe JavaScript

### Styling

- **Tailwind CSS**: Utility-first CSS framework
- **PostCSS**: CSS transformations

### Data Management

- **TanStack Query (React Query)**: Server state management for API calls, caching, and polling
- **Zod**: Runtime type validation for API responses

### Visualization

- **React Flow (@xyflow/react)**: Interactive knowledge graph visualization with pan, zoom, and node interaction

### Testing

- **Vitest**: Fast unit test runner with TypeScript support
- **@testing-library/react**: React component testing utilities
- **@testing-library/jest-dom**: Custom matchers for DOM assertions
- **Playwright**: End-to-end testing framework
- **jsdom**: DOM implementation for Node.js (used by Vitest)

### Utilities

- **uuid**: Generate unique identifiers for sessions and components

## Development Guidelines

### Code Quality

Run type checking before committing:

```bash
npm run type-check
```

Run linting:

```bash
npm run lint
```

### Styling

This project uses Tailwind CSS. Refer to the [Tailwind documentation](https://tailwindcss.com/docs) for available utility classes.

Example component:

```tsx
export default function Button() {
  return (
    <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
      Click me
    </button>
  );
}
```

### API Client

The API client is configured in `src/lib/api.ts`:

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

Example API call:

```typescript
import { api } from '@/lib/api';

const response = await api.get('/api/v1/health');
```

### React Query

TanStack Query is configured in `src/app/providers.tsx`. Use it for server state management:

```typescript
import { useQuery } from '@tanstack/react-query';

function MyComponent() {
  const { data, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => fetch('/api/v1/health').then(r => r.json()),
  });

  if (isLoading) return <div>Loading...</div>;
  return <div>{data.status}</div>;
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

All variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

## Building for Production

Build the application:

```bash
npm run build
```

Start the production server:

```bash
npm run start
```

The production build will be optimized and minified.

## Troubleshooting

### Port Already in Use

If port 3000 is in use, specify a different port:

```bash
PORT=3001 npm run dev
```

### Module Not Found Errors

Clear the cache and reinstall:

```bash
rm -rf node_modules .next
npm install
```

### TypeScript Errors

Run type checking to see detailed errors:

```bash
npm run type-check
```

### API Connection Issues

Ensure the backend is running and `NEXT_PUBLIC_API_URL` is correctly set in `.env.local`.

## Performance

### Next.js Optimizations

- Server Components by default (faster initial load)
- Automatic code splitting
- Image optimization with `next/image`
- Font optimization with `next/font`

### Best Practices

1. Use Server Components when possible
2. Mark interactive components with `'use client'`
3. Optimize images with `next/image`
4. Use React Query for data fetching
5. Leverage Tailwind for styling efficiency
