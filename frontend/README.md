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

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js App Router
│   │   ├── globals.css   # Global styles
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Home page
│   │   └── providers.tsx # React Query provider
│   └── lib/              # Shared utilities
│       └── api.ts        # API client
├── public/               # Static assets
├── .env.local           # Environment variables (not in git)
├── .env.local.example   # Example environment file
├── next.config.js       # Next.js configuration
├── tailwind.config.ts   # Tailwind CSS configuration
├── tsconfig.json        # TypeScript configuration
└── package.json         # Dependencies
```

## Technology Stack

### Core

- **Next.js 15+**: React framework with App Router
- **React 18**: UI library
- **TypeScript**: Type-safe JavaScript

### Styling

- **Tailwind CSS**: Utility-first CSS framework
- **PostCSS**: CSS transformations

### Data Management

- **TanStack Query (React Query)**: Server state management
- **Zod**: Runtime type validation

### Visualization

- **React Flow (@xyflow/react)**: Interactive knowledge graph visualization

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
