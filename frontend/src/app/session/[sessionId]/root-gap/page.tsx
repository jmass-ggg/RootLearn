'use client';

import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import AppShell from '@/components/AppShell';
import RootGapCard from '@/components/RootGapCard';
import PathSummary from '@/components/PathSummary';
import { StateDisplay } from '@/components/ui/StateDisplay';
import type { RootGapResult, PrerequisiteGraph } from '@/types';

export default function RootGapPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const sessionId = params.sessionId as string;
  const userId = searchParams.get('user_id');

  // Fetch session data
  const { 
    data: session,
    isLoading: sessionLoading,
  } = useQuery({
    queryKey: ['session', sessionId, userId],
    queryFn: () => api.sessions.get(sessionId, userId!),
    enabled: !!userId,
  });

  // Fetch root gap
  const { 
    data: rootGap,
    isLoading: rootGapLoading,
    error: rootGapError,
    refetch: refetchRootGap,
  } = useQuery({
    queryKey: ['root-gap', sessionId, userId],
    queryFn: () => api.rootGap.get(sessionId, userId!),
    enabled: !!userId,
    retry: 1,
  });

  // Fetch graph for path visualization
  const { data: graph } = useQuery({
    queryKey: ['graph', sessionId, userId],
    queryFn: () => api.graph.get(sessionId, userId!),
    enabled: !!userId,
    retry: 1,
  });

  const handleStartLearning = () => {
    // Navigate to tutor view - same session, same sessionId
    router.push(`/session/${sessionId}?user_id=${userId}`);
  };

  const handleRetry = () => {
    refetchRootGap();
  };

  const handleReturnHome = () => {
    router.push('/');
  };

  if (!userId) {
    return (
      <AppShell>
        <StateDisplay
          variant="error"
          title="Missing User ID"
          description="User ID is required to view this page."
          action={{
            label: 'Go Home',
            onClick: handleReturnHome,
          }}
        />
      </AppShell>
    );
  }

  if (sessionLoading || rootGapLoading) {
    return (
      <AppShell 
        status={session?.status} 
        topic={session?.normalized_topic || session?.original_prompt}
        activeSection="root-gap"
      >
        <StateDisplay
          variant="loading"
          title="Loading root gap analysis"
          description="Fetching your foundational knowledge gap..."
        />
      </AppShell>
    );
  }

  if (rootGapError || !rootGap) {
    const isError = !!rootGapError;
    return (
      <AppShell 
        status={session?.status} 
        topic={session?.normalized_topic || session?.original_prompt}
        activeSection="root-gap"
      >
        <StateDisplay
          variant={isError ? "error" : "empty"}
          title={isError ? "Failed to load root gap" : "No root gap identified"}
          description={
            isError 
              ? "There was an error loading your root gap analysis. Please try again."
              : "We couldn't identify a root knowledge gap for this session. This might mean your understanding is more complete than expected."
          }
          action={{
            label: isError ? 'Retry' : 'Return to Session',
            onClick: isError ? handleRetry : () => router.push(`/session/${sessionId}?user_id=${userId}`),
          }}
        />
      </AppShell>
    );
  }

  return (
    <AppShell 
      status={session?.status} 
      topic={session?.normalized_topic || session?.original_prompt}
      activeSection="root-gap"
    >
      <section className="min-h-[calc(100vh-76px)] px-4 py-10 sm:px-8">
        <div className="mx-auto max-w-5xl text-center">
          <span className="rounded-full bg-[#ddf4ea] px-4 py-2 text-sm font-semibold text-[#18986b]">
            ✓ Diagnosis complete
          </span>
          <h1 className="mt-6 text-4xl font-bold tracking-tight">
            We found the foundational gap
          </h1>
          <p className="mx-auto mt-3 max-w-2xl text-lg text-[#718096]">
            Pinpointing the real starting point means the rest can click into place much faster.
          </p>
        </div>
        
        <div className="mx-auto mt-10 max-w-5xl">
          <RootGapCard 
            rootGap={rootGap} 
            isLoading={false} 
            onFixGap={handleStartLearning} 
          />
          
          {/* Path summary visualization */}
          <PathSummary graph={graph} rootGap={rootGap} />
        </div>
      </section>
    </AppShell>
  );
}
