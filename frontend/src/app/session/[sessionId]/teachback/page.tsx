'use client';

import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { api, APIError } from '@/lib/api';
import { SessionShell } from '@/components/layout/SessionShell';
import { StateDisplay } from '@/components/ui/StateDisplay';
import TeachBackPanel from '@/components/TeachBackPanel';

/**
 * Teach-Back Page - Focused verification interface
 * Requirements: 9.1
 * 
 * Uses SessionShell with Teach-Back section highlighted
 * Displays focused verification interface with centered Card
 */
export default function TeachBackPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();

  const sessionId = params.sessionId as string;
  const userId = searchParams.get('user_id');

  // Mutation for submitting teach-back explanation - MUST be at top level
  const submitExplanationMutation = useMutation({
    mutationFn: async (explanation: string) => {
      if (!userId || !sessionId) {
        throw new Error('Missing required parameters');
      }
      
      // Get current concept from tutor data
      const tutorResponse = await api.tutor.getMessages(sessionId, userId);
      if (!tutorResponse?.concept_id) {
        throw new Error('No current concept');
      }
      
      return api.teachback.submit(sessionId, {
        user_id: userId,
        concept_id: tutorResponse.concept_id,
        explanation,
      });
    },
    onSuccess: () => {
      if (userId && sessionId) {
        queryClient.invalidateQueries({ queryKey: ['graph', sessionId, userId] });
        queryClient.invalidateQueries({ queryKey: ['session', sessionId, userId] });
      }
    },
  });

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
    enabled: !!userId && session?.status === 'teachback',
    refetchInterval: 15000,
  });

  // Fetch tutor data for current concept
  const { data: tutorData } = useQuery({
    queryKey: ['tutor-messages', sessionId, userId],
    queryFn: () => api.tutor.getMessages(sessionId, userId!),
    enabled: !!userId && session?.status === 'teachback',
  });

  // Handle missing user ID
  if (!userId) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <StateDisplay
          variant="error"
          title="Missing User ID"
          description="User ID is required to view this teach-back session."
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
          title="Loading teach-back session..."
          description="Please wait while we prepare your verification experience."
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
              : 'Failed to load teach-back session. Please try again.'
          }
          action={{
            label: 'Return to Session',
            onClick: () => router.push(`/session/${sessionId}?user_id=${userId}`),
          }}
        />
      </div>
    );
  }

  // Redirect if not in teachback state
  if (session && session.status !== 'teachback') {
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

  // Handle continue action (navigate based on evaluation result)
  const handleContinue = () => {
    // Navigate back to main session page which will handle state routing
    router.push(`/session/${sessionId}?user_id=${userId}`);
  };

  // Handle retry action (clear evaluation and allow retry)
  const handleRetry = () => {
    submitExplanationMutation.reset();
  };

  return (
    <SessionShell
      sessionId={sessionId}
      userId={userId}
      currentPhase="teachback"
      topic={session.normalized_topic || session.original_prompt}
    >
      {/* Centered focused verification interface */}
      <div className="flex justify-center items-start min-h-[calc(100vh-200px)]">
        <div className="w-full max-w-3xl">
          <TeachBackPanel
            currentConcept={currentConcept}
            masteryScore={masteryScore}
            confidenceScore={confidenceScore}
            evaluation={submitExplanationMutation.data || null}
            isLoading={submitExplanationMutation.isPending}
            error={submitExplanationMutation.error}
            onSubmitExplanation={async (explanation) => {
              return await submitExplanationMutation.mutateAsync(explanation);
            }}
            onContinue={handleContinue}
            onRetry={handleRetry}
          />
        </div>
      </div>
    </SessionShell>
  );
}
