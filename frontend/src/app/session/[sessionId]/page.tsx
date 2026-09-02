'use client';

import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { api, APIError } from '@/lib/api';
import { SessionResponse } from '@/lib/api';
import KnowledgeGraph from '@/components/KnowledgeGraph';
import DiagnosticPanel from '@/components/DiagnosticPanel';
import RootGapCard from '@/components/RootGapCard';
import TutorPanel from '@/components/TutorPanel';
import TeachBackPanel from '@/components/TeachBackPanel';
import { useEffect, useState } from 'react';

export default function SessionPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  
  const sessionId = params.sessionId as string;
  const userId = searchParams.get('user_id');

  // State for tracking transitions
  const [previousStatus, setPreviousStatus] = useState<string | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Fetch session data with polling to catch status changes
  const { 
    data: session, 
    isLoading: sessionLoading, 
    error: sessionError,
    refetch: refetchSession 
  } = useQuery({
    queryKey: ['session', sessionId, userId],
    queryFn: () => api.sessions.get(sessionId, userId!),
    enabled: !!userId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'abandoned') {
        return false;
      }
      if (status === 'analyzing') {
        return 3000;
      }
      return 10000;
    },
    retry: 2,
  });

  // Fetch graph data
  const { 
    data: graph, 
    isLoading: graphLoading,
    error: graphError,
    refetch: refetchGraph 
  } = useQuery({
    queryKey: ['graph', sessionId, userId],
    queryFn: () => api.graph.get(sessionId, userId!),
    enabled: !!userId && !!session && session.status !== 'analyzing',
    retry: (failureCount, error) => {
      if (error instanceof APIError && error.status === 404) {
        return false;
      }
      return failureCount < 2;
    },
    refetchInterval: (query) => {
      const status = session?.status;
      if (status === 'diagnosing' || status === 'tutoring' || status === 'teachback') {
        return 15000;
      }
      return false;
    },
  });

  // Fetch current diagnostic question
  const { 
    data: currentQuestion,
    isLoading: questionLoading,
  } = useQuery({
    queryKey: ['diagnostic-question', sessionId, userId],
    queryFn: () => api.diagnosis.getCurrentQuestion(sessionId, userId!),
    enabled: !!userId && session?.status === 'diagnosing',
    retry: (failureCount, error) => {
      if (error instanceof APIError && error.status === 404) {
        return false;
      }
      return failureCount < 2;
    },
  });

  // Fetch root gap
  const { 
    data: rootGap,
    isLoading: rootGapLoading,
    refetch: refetchRootGap,
  } = useQuery({
    queryKey: ['root-gap', sessionId, userId],
    queryFn: () => api.rootGap.get(sessionId, userId!),
    enabled: !!userId && (session?.status === 'tutoring' || session?.status === 'teachback'),
    retry: false,
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

  // State for evaluation
  const [lastEvaluation, setLastEvaluation] = useState<any>(null);
  const [teachBackEvaluation, setTeachBackEvaluation] = useState<any>(null);
  const [isRequestingTeachback, setIsRequestingTeachback] = useState(false);

  // Mutation for submitting diagnostic answers
  const submitAnswerMutation = useMutation({
    mutationFn: (answer: string) => 
      api.diagnosis.submitAnswer(sessionId, { 
        user_id: userId!, 
        question_id: currentQuestion?.question_id || '',
        answer 
      }),
    onSuccess: (evaluation) => {
      setLastEvaluation(evaluation);
      queryClient.invalidateQueries({ queryKey: ['diagnostic-question', sessionId, userId] });
      queryClient.invalidateQueries({ queryKey: ['graph', sessionId, userId] });
      
      if (evaluation.should_stop) {
        setTimeout(() => {
          queryClient.invalidateQueries({ queryKey: ['session', sessionId, userId] });
        }, 2000);
      }
    },
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
      // Invalidate session to trigger status update
      queryClient.invalidateQueries({ queryKey: ['session', sessionId, userId] });
    },
  });

  // Mutation for submitting teach-back
  const submitTeachBackMutation = useMutation({
    mutationFn: (explanation: string) =>
      api.teachback.submit(sessionId, {
        user_id: userId!,
        concept_id: tutorData?.concept_id || '',
        explanation,
      }),
    onSuccess: (result) => {
      setTeachBackEvaluation(result);
      queryClient.invalidateQueries({ queryKey: ['graph', sessionId, userId] });
      
      // Trigger session status check after a delay to catch state transitions
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['session', sessionId, userId] });
      }, 2000);
    },
  });

  // Reset evaluation when question changes
  useEffect(() => {
    if (currentQuestion) {
      setLastEvaluation(null);
    }
  }, [currentQuestion?.question_id]); // Only depend on question_id, not the whole object

  // Reset teach-back evaluation when status changes
  useEffect(() => {
    if (session?.status !== 'teachback') {
      setTeachBackEvaluation(null);
    }
  }, [session?.status]);

  // Handle state transitions after teach-back
  useEffect(() => {
    if (teachBackEvaluation && session) {
      // Check if we've transitioned away from teachback state
      const checkTransition = setTimeout(() => {
        if (session.status !== 'teachback') {
          // Clear evaluation since we've moved on
          setTeachBackEvaluation(null);
        }
      }, 3000);

      return () => clearTimeout(checkTransition);
    }
  }, [teachBackEvaluation, session]);

  // Track state transitions
  useEffect(() => {
    if (session?.status) {
      if (previousStatus && previousStatus !== session.status) {
        // State has changed
        setIsTransitioning(true);
        
        // Invalidate relevant queries based on new state
        if (session.status === 'diagnosing') {
          queryClient.invalidateQueries({ queryKey: ['diagnostic-question', sessionId, userId] });
        } else if (session.status === 'tutoring') {
          queryClient.invalidateQueries({ queryKey: ['root-gap', sessionId, userId] });
          queryClient.invalidateQueries({ queryKey: ['tutor-messages', sessionId, userId] });
        } else if (session.status === 'teachback') {
          setTeachBackEvaluation(null); // Clear any previous evaluation
        }
        
        // Clear transitioning state after animation
        const timer = setTimeout(() => {
          setIsTransitioning(false);
        }, 1000);
        
        return () => clearTimeout(timer);
      }
      setPreviousStatus(session.status);
    }
  }, [session?.status, previousStatus, sessionId, userId, queryClient]);

  // Invalidate graph when session status changes
  useEffect(() => {
    if (session?.status && session.status !== 'analyzing') {
      queryClient.invalidateQueries({ queryKey: ['graph', sessionId, userId] });
    }
  }, [session?.status, sessionId, userId, queryClient]);

  if (!userId) {
    return (
      <ErrorDisplay 
        title="Missing User ID"
        message="User ID is required to view this session."
        onRetry={() => router.push('/')}
        retryLabel="Go Home"
      />
    );
  }

  if (sessionLoading) {
    return <LoadingDisplay message="Loading your learning session..." />;
  }

  if (sessionError) {
    return (
      <ErrorDisplay 
        title="Session Error"
        message={
          sessionError instanceof APIError 
            ? sessionError.message 
            : 'Failed to load session. Please try again.'
        }
        onRetry={refetchSession}
      />
    );
  }

  if (!session) {
    return null;
  }

  // Get current concept from tutor data if available
  const currentConcept = tutorData ? {
    id: tutorData.concept_id,
    name: tutorData.concept_name,
  } : null;

  const masteryScore = tutorData ? 
    graph?.concepts.find(c => c.id === tutorData.concept_id)?.mastery_score || 0 : 0;
  const confidenceScore = tutorData ?
    graph?.concepts.find(c => c.id === tutorData.concept_id)?.confidence_score || 0 : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold text-gray-900">RootLearn</h1>
              <p className="text-sm text-gray-600 mt-1 truncate">
                {session.normalized_topic || session.original_prompt || 'Analyzing your learning needs...'}
              </p>
            </div>
            <div className="flex items-center gap-4 flex-shrink-0">
              <StatusBadge status={session.status} />
              <button
                onClick={() => router.push('/')}
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors whitespace-nowrap"
              >
                New Session
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* State transition indicator */}
        {isTransitioning && (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center gap-3 animate-pulse">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <p className="text-sm text-blue-800 font-medium">
              Transitioning to {session?.status}...
            </p>
          </div>
        )}

        {/* State guidance */}
        {!isTransitioning && session?.status && (
          <StateGuidance status={session.status} />
        )}
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left side: Knowledge Graph */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                Knowledge Map
              </h2>
            </div>
            <div className="h-[600px]">
              {graphLoading ? (
                <LoadingDisplay message="Building your knowledge map..." compact />
              ) : graphError ? (
                <div className="flex items-center justify-center h-full p-6">
                  <div className="text-center">
                    <p className="text-gray-500 mb-3">
                      {graphError instanceof APIError && graphError.status === 404
                        ? 'Knowledge map is being generated...'
                        : 'Failed to load knowledge map'}
                    </p>
                    {!(graphError instanceof APIError && graphError.status === 404) && (
                      <button
                        onClick={() => refetchGraph()}
                        className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                      >
                        Retry
                      </button>
                    )}
                  </div>
                </div>
              ) : graph ? (
                <KnowledgeGraph graph={graph} />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p className="text-gray-500">No knowledge graph available yet</p>
                </div>
              )}
            </div>
          </div>

          {/* Right side: Dynamic panel based on session status */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            {session.status === 'analyzing' && (
              <div className="flex flex-col items-center justify-center h-[600px] p-6">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mb-4"></div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Analyzing Your Learning Needs
                </h3>
                <p className="text-gray-600 text-center max-w-md">
                  We&apos;re identifying the target concept and building a prerequisite graph...
                </p>
              </div>
            )}

            {session.status === 'diagnosing' && (
              <div className="flex flex-col h-[600px]">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">
                    Diagnostic Assessment
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Answer questions to help us understand your current knowledge
                  </p>
                </div>
                <div className="flex-1 overflow-auto p-6">
                  <DiagnosticPanel
                    question={currentQuestion || null}
                    evaluation={lastEvaluation}
                    isLoading={questionLoading}
                    onSubmitAnswer={async (answer) => {
                      await submitAnswerMutation.mutateAsync(answer);
                    }}
                  />
                </div>
              </div>
            )}

            {session.status === 'tutoring' && (
              <div className="flex flex-col h-[600px]">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">
                    Socratic Tutoring
                  </h2>
                  <RootGapCard
                    rootGap={rootGap || null}
                    isLoading={rootGapLoading}
                    onFixGap={() => {
                      // Already in tutoring mode, this button might not be needed
                      console.log('Fix gap clicked');
                    }}
                  />
                </div>
                <div className="flex-1 overflow-hidden">
                  <TutorPanel
                    sessionId={sessionId}
                    userId={userId}
                    messages={tutorData?.messages || []}
                    currentConcept={currentConcept}
                    masteryScore={masteryScore}
                    confidenceScore={confidenceScore}
                    isLoading={tutorLoading}
                    onSendMessage={async (message) => {
                      return await sendMessageMutation.mutateAsync(message);
                    }}
                    onExplainBack={async () => {
                      setIsRequestingTeachback(true);
                      try {
                        await requestTeachbackMutation.mutateAsync();
                      } finally {
                        setIsRequestingTeachback(false);
                      }
                    }}
                  />
                </div>
              </div>
            )}

            {session.status === 'teachback' && (
              <div className="flex flex-col h-[600px]">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">
                    Teach-Back Verification
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Explain the concept in your own words to verify your understanding
                  </p>
                  {currentConcept && (
                    <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm font-medium text-blue-900">
                        Current Concept: {currentConcept.name}
                      </p>
                      <div className="mt-2 flex items-center gap-4">
                        <div>
                          <span className="text-xs text-blue-700">Mastery: </span>
                          <span className="text-sm font-semibold text-blue-900">
                            {Math.round(masteryScore * 100)}%
                          </span>
                        </div>
                        <div>
                          <span className="text-xs text-blue-700">Confidence: </span>
                          <span className="text-sm font-semibold text-blue-900">
                            {Math.round(confidenceScore * 100)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <div className="flex-1 overflow-auto p-6">
                  <TeachBackPanel
                    currentConcept={currentConcept}
                    masteryScore={masteryScore}
                    confidenceScore={confidenceScore}
                    evaluation={teachBackEvaluation}
                    isLoading={submitTeachBackMutation.isPending}
                    onSubmitExplanation={async (explanation) => {
                      return await submitTeachBackMutation.mutateAsync(explanation);
                    }}
                    onContinue={() => {
                      // Force a session status check
                      refetchSession();
                    }}
                  />
                </div>
              </div>
            )}

            {session.status === 'completed' && (
              <div className="flex flex-col items-center justify-center h-[600px] p-6">
                <div className="text-center">
                  <svg 
                    className="w-20 h-20 text-green-500 mx-auto mb-4" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
                    />
                  </svg>
                  <h3 className="text-2xl font-semibold text-gray-900 mb-2">
                    Learning Complete!
                  </h3>
                  <p className="text-gray-600 max-w-md">
                    You&apos;ve successfully worked through your knowledge gaps.
                  </p>
                </div>
              </div>
            )}

            {session.status === 'abandoned' && (
              <div className="flex flex-col items-center justify-center h-[600px] p-6">
                <div className="text-center">
                  <svg 
                    className="w-20 h-20 text-gray-400 mx-auto mb-4" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M6 18L18 6M6 6l12 12" 
                    />
                  </svg>
                  <h3 className="text-2xl font-semibold text-gray-900 mb-2">
                    Session Abandoned
                  </h3>
                  <p className="text-gray-600 max-w-md">
                    This learning session was not completed.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { label: string; color: string; pulse?: boolean }> = {
    analyzing: { label: 'Analyzing', color: 'bg-blue-100 text-blue-800', pulse: true },
    diagnosing: { label: 'Diagnosing', color: 'bg-purple-100 text-purple-800' },
    tutoring: { label: 'Tutoring', color: 'bg-green-100 text-green-800' },
    teachback: { label: 'Teach-Back', color: 'bg-yellow-100 text-yellow-800' },
    completed: { label: 'Completed', color: 'bg-gray-100 text-gray-800' },
    abandoned: { label: 'Abandoned', color: 'bg-red-100 text-red-800' },
  };

  const config = statusConfig[status] || { label: status, color: 'bg-gray-100 text-gray-800' };

  return (
    <div className="flex items-center gap-2">
      {config.pulse && (
        <span className="relative flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
        </span>
      )}
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${config.color} whitespace-nowrap`}>
        {config.label}
      </span>
    </div>
  );
}

function StateGuidance({ status }: { status: string }) {
  const guidance: Record<string, { title: string; description: string; icon: string }> = {
    diagnosing: {
      title: 'Diagnostic Phase',
      description: 'Answer questions to help us identify your knowledge gaps.',
      icon: '🔍',
    },
    tutoring: {
      title: 'Learning Phase',
      description: 'We\'re helping you understand the foundational concept you need.',
      icon: '💡',
    },
    teachback: {
      title: 'Verification Phase',
      description: 'Explain what you\'ve learned in your own words to demonstrate understanding.',
      icon: '✍️',
    },
    completed: {
      title: 'Session Complete',
      description: 'You\'ve successfully addressed your knowledge gaps!',
      icon: '🎉',
    },
  };

  const config = guidance[status];
  if (!config) return null;

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 mb-6">
      <div className="flex items-start gap-3">
        <span className="text-3xl">{config.icon}</span>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{config.title}</h3>
          <p className="text-sm text-gray-600 mt-1">{config.description}</p>
        </div>
      </div>
    </div>
  );
}

function LoadingDisplay({ message, compact = false }: { message: string; compact?: boolean }) {
  return (
    <div className={`flex items-center justify-center ${compact ? 'h-full' : 'min-h-screen'}`}>
      <div className="text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">{message}</p>
      </div>
    </div>
  );
}

function ErrorDisplay({ 
  title, 
  message, 
  onRetry,
  retryLabel = 'Try Again'
}: { 
  title: string; 
  message: string; 
  onRetry: () => void;
  retryLabel?: string;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-gray-50">
      <div className="text-center max-w-md">
        <div className="mb-4">
          <svg 
            className="w-16 h-16 text-red-500 mx-auto" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
            />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">{title}</h2>
        <p className="text-gray-600 mb-6">{message}</p>
        <button
          onClick={onRetry}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
        >
          {retryLabel}
        </button>
      </div>
    </div>
  );
}
