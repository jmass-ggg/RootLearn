'use client';

import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { api, APIError } from '@/lib/api';
import { SessionShell } from '@/components/layout/SessionShell';
import { StateDisplay } from '@/components/ui/StateDisplay';
import TutorPanel from '@/components/TutorPanel';
import TutorContextPanel from '@/components/TutorContextPanel';

/**
 * Tutor Page - AI Socratic tutoring interface
 * Requirements: 8.1, 8.2, 13.2
 * 
 * Desktop layout: compact left column | wide right conversation panel
 * Mobile layout: single column
 */
export default function TutorPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();

  const sessionId = params.sessionId as string;
  const userId = searchParams.get('user_id');

  // Fetch session data
  const {
    data: session,
    isLoading: sessionLoading,
    error: sessionError,
  } = useQuery({
    queryKey: ['session', sessionId, userId],
    queryFn: () => api.sessions.get(sessionId, userId!),
    enabled: !!userId,
    refetchInterval: 10000,
  });

  // Fetch graph data for mastery scores
  const { data: graph } = useQuery({
    queryKey: ['graph', sessionId, userId],
    queryFn: () => api.graph.get(sessionId, userId!),
    enabled: !!userId && session?.status === 'tutoring',
    refetchInterval: 15000,
  });

  // Fetch tutor messages
  const {
    data: tutorData,
    isLoading: tutorLoading,
  } = useQuery({
    queryKey: ['tutor-messages', sessionId, userId],
    queryFn: () => api.tutor.getMessages(sessionId, userId!),
    enabled: !!userId && session?.status === 'tutoring',
    refetchInterval: 5000,
  });

  // Fetch root gap for context
  const { data: rootGap } = useQuery({
    queryKey: ['root-gap', sessionId, userId],
    queryFn: () => api.rootGap.get(sessionId, userId!),
    enabled: !!userId && session?.status === 'tutoring',
  });

  // Mutation for sending tutor messages
  const sendMessageMutation = useMutation({
    mutationFn: (message: string) =>
      api.tutor.sendMessage(sessionId, { user_id: userId!, message }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tutor-messages', sessionId, userId] });
      queryClient.invalidateQueries({ queryKey: ['graph', sessionId, userId] });
    },
  });

  // Mutation for requesting teachback transition
  const requestTeachbackMutation = useMutation({
    mutationFn: () => api.tutor.requestTeachback(sessionId, userId!),
    onSuccess: () => {
      // Navigate to main session page which will show teachback state
      router.push(`/session/${sessionId}?user_id=${userId}`);
    },
  });

  // Handle missing user ID
  if (!userId) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <StateDisplay
          variant="error"
          title="Missing User ID"
          description="User ID is required to view this tutoring session."
          action={{
            label: 'Go Home',
            onClick: () => router.push('/'),
          }}
        />
      </div>
    );
  }

  // Loading state
  if (sessionLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <StateDisplay
          variant="loading"
          title="Loading tutoring session..."
          description="Please wait while we prepare your learning experience."
        />
      </div>
    );
  }

  // Error state
  if (sessionError) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <StateDisplay
          variant="error"
          title="Session Error"
          description={
            sessionError instanceof APIError
              ? sessionError.message
              : 'Failed to load tutoring session. Please try again.'
          }
          action={{
            label: 'Return to Session',
            onClick: () => router.push(`/session/${sessionId}?user_id=${userId}`),
          }}
        />
      </div>
    );
  }

  // Redirect if not in tutoring state
  if (session && session.status !== 'tutoring') {
    router.push(`/session/${sessionId}?user_id=${userId}`);
    return null;
  }

  if (!session) {
    return null;
  }

  // Get current concept from tutor data
  const currentConcept = tutorData
    ? {
        id: tutorData.concept_id,
        name: tutorData.concept_name,
      }
    : null;

  // Get mastery scores from graph
  const conceptData = graph?.concepts.find((c) => c.id === tutorData?.concept_id);
  const masteryScore = conceptData?.mastery_score || 0;
  const confidenceScore = conceptData?.confidence_score || 0;

  return (
    <SessionShell
      sessionId={sessionId}
      userId={userId}
      currentPhase="tutoring"
      topic={session.normalized_topic || session.original_prompt}
    >
      {/* Desktop: two-column layout (compact left | wide right) */}
      {/* Mobile: single-column layout */}
      <div className="flex flex-col xl:flex-row gap-4 sm:gap-6 h-full min-h-[calc(100vh-200px)] max-w-[1600px] mx-auto w-full">
        {/* Left column: Compact context panel */}
        <aside className="w-full xl:w-80 flex-shrink-0 min-w-0">
          <TutorContextPanel
            currentConcept={currentConcept}
            masteryScore={masteryScore}
            confidenceScore={confidenceScore}
            rootGap={rootGap || null}
            graph={graph}
          />
        </aside>

        {/* Right column: Main conversation panel */}
        <main className="flex-1 min-w-0 w-full">
          <div className="bg-white rounded-xl shadow-sm border border-border overflow-hidden h-full min-h-[500px]">
            <TutorPanel
              sessionId={sessionId}
              userId={userId}
              messages={tutorData?.messages || []}
              currentConcept={currentConcept}
              masteryScore={masteryScore}
              confidenceScore={confidenceScore}
              isLoading={tutorLoading}
              onSendMessage={(message) => sendMessageMutation.mutateAsync(message)}
              onExplainBack={async () => {
                await requestTeachbackMutation.mutateAsync();
              }}
            />
          </div>
        </main>
      </div>
    </SessionShell>
  );
}
