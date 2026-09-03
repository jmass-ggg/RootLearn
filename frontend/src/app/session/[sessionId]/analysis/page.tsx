'use client';

import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FadeIn } from '@/components/ui/FadeTransition';
import { useEffect } from 'react';

interface ProgressStep {
  title: string;
  description: string;
  state: 'completed' | 'active' | 'pending';
}

function ProgressSteps({ steps }: { steps: ProgressStep[] }) {
  return (
    <ol className="space-y-6">
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1;
        
        return (
          <li key={step.title} className="relative flex gap-4">
            {/* Connecting line */}
            {!isLast && (
              <span className="absolute left-[18px] top-9 h-10 w-px bg-[#dbe4ef]" />
            )}
            
            {/* Step indicator */}
            <span
              className={`relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 ${
                step.state === 'completed'
                  ? 'border-mastery-mastered bg-mastery-mastered text-white'
                  : step.state === 'active'
                  ? 'animate-pulse border-brand-blue bg-white text-brand-blue'
                  : 'border-[#dbe4ef] bg-white text-text-muted'
              }`}
            >
              {step.state === 'completed' ? (
                '✓'
              ) : step.state === 'active' ? (
                <svg
                  className="h-5 w-5 animate-spin"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              ) : (
                '○'
              )}
            </span>
            
            {/* Step content */}
            <div className="flex-1">
              <p
                className={`font-semibold ${
                  step.state === 'active'
                    ? 'text-brand-blue'
                    : step.state === 'completed'
                    ? 'text-text-heading'
                    : 'text-text-body'
                }`}
              >
                {step.title}
              </p>
              <p className="mt-0.5 text-sm text-text-muted">{step.description}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

export default function AnalysisPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const sessionId = params.sessionId as string;
  const userId = searchParams.get('user_id');

  // Fetch session data with polling
  const { data: session, isLoading } = useQuery({
    queryKey: ['session', sessionId, userId],
    queryFn: () => api.sessions.get(sessionId, userId!),
    enabled: !!userId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Poll every 3 seconds while analyzing
      if (status === 'analyzing') {
        return 3000;
      }
      // Stop polling once analysis is complete
      return false;
    },
    retry: 2,
  });

  // Determine progress steps based on session status
  // Since we don't have granular analysis progress from backend,
  // we'll use a heuristic - show first 2 complete, 3rd active, 4th pending
  // This matches the existing AnalyzingView behavior
  const getProgressSteps = (): ProgressStep[] => {
    return [
      {
        title: 'Understanding the learner\'s topic',
        description: topic ? `Parsed your description of ${topic}` : 'Parsed your learning goal',
        state: 'completed',
      },
      {
        title: 'Identifying the target concept',
        description: 'Locating the goal in the domain graph',
        state: 'completed',
      },
      {
        title: 'Building prerequisite relationships',
        description: 'Connecting the concepts you need first…',
        state: 'active',
      },
      {
        title: 'Preparing the diagnostic assessment',
        description: 'Waiting for the knowledge map',
        state: 'pending',
      },
    ];
  };

  const steps = getProgressSteps();

  // Auto-transition when status changes from 'analyzing'
  useEffect(() => {
    if (session && session.status !== 'analyzing') {
      // Navigate based on new status
      if (session.status === 'diagnosing') {
        router.push(`/session/${sessionId}?user_id=${userId}`);
      } else if (session.status === 'tutoring') {
        router.push(`/session/${sessionId}?user_id=${userId}`);
      } else if (session.status === 'teachback') {
        router.push(`/session/${sessionId}?user_id=${userId}`);
      } else if (session.status === 'completed' || session.status === 'abandoned') {
        router.push(`/session/${sessionId}?user_id=${userId}`);
      }
    }
  }, [session, sessionId, userId, router]);

  if (!userId) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <Card className="text-center max-w-md">
          <h2 className="text-2xl font-bold text-text-heading mb-2">Missing User ID</h2>
          <p className="text-text-body mb-6">User ID is required to view this session.</p>
          <Button onClick={() => router.push('/')}>Go Home</Button>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-brand-blue mx-auto mb-4"></div>
          <p className="text-text-body">Loading session...</p>
        </div>
      </div>
    );
  }

  const topic = session?.normalized_topic || session?.original_prompt || 'your topic';

  return (
    <section className="min-h-screen bg-bg-workspace flex flex-col items-center justify-center px-5 py-12">
      <Card className="w-full max-w-[670px]" padding="xl">
        {/* Header */}
        <div className="text-center">
          <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-full border-2 border-[#9dbaff] bg-[#f1f6ff] text-2xl text-brand-blue">
            ⌘
          </span>
          <h1 className="mt-6 text-3xl font-bold text-text-heading">
            Analyzing your topic
          </h1>
          <p className="mt-2 text-lg text-text-body">
            Building your prerequisite knowledge map
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mt-10">
          <ProgressSteps steps={steps} />
        </div>

        {/* Footer with timing info */}
        <div className="mt-9 border-t border-border-default pt-7 text-center">
          <p className="text-lg font-semibold text-text-heading">
            Mapping what you need to know first…
          </p>
          <p className="mt-2 text-sm text-text-muted">
            ◷ Mapping usually takes about a minute
          </p>
        </div>
      </Card>

      {/* Cancel button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.push('/')}
        className="mt-7"
      >
        Cancel and return home
      </Button>
    </section>
  );
}
