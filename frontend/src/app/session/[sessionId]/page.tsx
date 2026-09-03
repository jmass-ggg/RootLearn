'use client';

import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { api, APIError } from '@/lib/api';
import { SessionResponse } from '@/lib/api';
import KnowledgeGraph from '@/components/KnowledgeGraph';
import { KnowledgeMapCard } from '@/components/KnowledgeMapCard';
import DiagnosticAssessmentCard from '@/components/DiagnosticAssessmentCard';
import RootGapCard from '@/components/RootGapCard';
import TutorPanel from '@/components/TutorPanel';
import TeachBackPanel from '@/components/TeachBackPanel';
import AppShell, { WorkspaceSection } from '@/components/AppShell';
import type { PrerequisiteGraph, RootGapResult, MasteryEvent } from '@/types';
import { useEffect, useState, useRef } from 'react';
import { FadeTransition } from '@/components/ui/FadeTransition';
import { smoothScrollToTop } from '@/lib/scroll-utils';

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

  // Fetch mastery events for completed sessions
  const { 
    data: masteryEvents,
    isLoading: masteryLoading,
  } = useQuery({
    queryKey: ['mastery-events', sessionId, userId],
    queryFn: () => api.mastery.getSessionEvents(sessionId, userId!),
    enabled: !!userId && session?.status === 'completed',
  });

  // State for evaluation
  const [lastEvaluation, setLastEvaluation] = useState<any>(null);
  const [teachBackEvaluation, setTeachBackEvaluation] = useState<any>(null);
  const [isRequestingTeachback, setIsRequestingTeachback] = useState(false);
  const [showTutor, setShowTutor] = useState(false);

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
  }, [currentQuestion]);

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
        
        // Smooth scroll to top when state changes (Requirements: 15.5)
        // This helps users see the new content without disorientation
        smoothScrollToTop();
        
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
      <div className="min-h-screen flex items-center justify-center p-8 bg-[#f4f7fb]">
        <div className="soft-card max-w-md p-10 text-center">
          <div className="mb-6">
            <svg className="w-16 h-16 text-[#e8a12d] mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-[#10213d] mb-2">Missing User ID</h2>
          <p className="text-[#718096] mb-4">
            User ID is required to view this session. This usually means you accessed this page directly without going through the proper flow.
          </p>
          
          <div className="rounded-xl bg-[#f8fafc] border border-[#dfe6ef] p-4 mb-6">
            <p className="text-sm text-[#718096]">
              Please start a new session from the home page to continue learning.
            </p>
          </div>

          <button
            onClick={() => router.push('/')}
            className="w-full rounded-xl bg-[#1463ff] px-6 py-3 font-semibold text-white hover:bg-[#0d4fc7] transition-colors"
          >
            Go to Home
          </button>
        </div>
      </div>
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
        error={sessionError}
        onRetry={refetchSession}
      />
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8 bg-[#f4f7fb]">
        <div className="soft-card max-w-md p-10 text-center">
          <div className="mb-6">
            <svg className="w-16 h-16 text-[#8792a5] mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-[#10213d] mb-2">Session Not Found</h2>
          <p className="text-[#718096] mb-4">
            The session you&apos;re looking for doesn&apos;t exist or has been deleted.
          </p>
          
          <div className="rounded-xl bg-[#f8fafc] border border-[#dfe6ef] p-4 mb-6">
            <p className="text-sm text-[#718096]">
              Start a new learning session to continue.
            </p>
          </div>

          <button
            onClick={() => router.push('/new-session')}
            className="w-full rounded-xl bg-[#1463ff] px-6 py-3 font-semibold text-white hover:bg-[#0d4fc7] transition-colors"
          >
            Start New Session
          </button>
        </div>
      </div>
    );
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

  const activeSection: WorkspaceSection = session.status === 'tutoring' && showTutor ? 'ai-tutor' :
    session.status === 'tutoring' ? 'root-gap' : session.status === 'diagnosing' ? 'diagnosis' :
    session.status === 'teachback' ? 'teach-back' : session.status === 'completed' ? 'progress' : 'overview';

  const graphPanel = (
    <GraphPanel
      graph={graph}
      isLoading={graphLoading}
      error={graphError}
      onRetry={() => refetchGraph()}
      topic={session.normalized_topic || session.original_prompt}
    />
  );

  return (
    <AppShell status={session.status} topic={session.normalized_topic || session.original_prompt} activeSection={activeSection} onNewSession={() => router.push('/new-session')}>
      {isTransitioning && (
        <div className="fixed right-6 top-24 z-50 flex items-center gap-3 rounded-xl border border-[#bcd0ff] bg-white px-4 py-3 text-sm font-semibold text-[#1463ff] shadow-lg">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-[#9dbaff] border-t-[#1463ff]" />
          Preparing the {session.status} stage…
        </div>
      )}

      {/* Wrap each status view in FadeTransition for smooth state changes (Requirements: 15.3) */}
      <FadeTransition transitionKey={session.status} duration={250}>
        {session.status === 'analyzing' && <AnalyzingView topic={session.normalized_topic || session.original_prompt} onCancel={() => router.push('/')} />}

        {session.status === 'diagnosing' && (
          <section className="flex flex-col lg:flex-row gap-6 p-4 sm:p-6 lg:p-8 max-w-[1600px] mx-auto">
            {/* Left column (or top on mobile): Knowledge Map */}
            <div className="w-full lg:w-1/2 xl:w-3/5 min-w-0">
              {graphPanel}
            </div>
            
            {/* Right column (or bottom on mobile): Diagnostic Assessment */}
            <div className="w-full lg:w-1/2 xl:w-2/5 min-w-0">
              <DiagnosticAssessmentCard 
                question={currentQuestion || null} 
                evaluation={lastEvaluation} 
                isLoading={questionLoading} 
                onSubmitAnswer={async (answer) => { 
                  await submitAnswerMutation.mutateAsync(answer); 
                }} 
              />
            </div>
          </section>
        )}

        {session.status === 'tutoring' && !showTutor && (
          <RootGapView rootGap={rootGap || null} graph={graph} isLoading={rootGapLoading} onContinue={() => setShowTutor(true)} />
        )}

        {session.status === 'tutoring' && showTutor && (
          <section className="mx-auto grid min-h-[calc(100vh-76px)] w-full max-w-[1600px] gap-4 sm:gap-6 p-4 sm:p-6 lg:p-7 xl:grid-cols-[340px_1fr]">
            <LearningPath graph={graph} rootGap={rootGap || null} />
            <div className="soft-card min-h-[600px] lg:min-h-[760px] overflow-hidden w-full min-w-0">
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
                  setIsRequestingTeachback(true);
                  try { await requestTeachbackMutation.mutateAsync(); } finally { setIsRequestingTeachback(false); }
                }}
              />
              {isRequestingTeachback && <p className="px-8 pb-5 text-sm text-[#1463ff]">Preparing teach-back…</p>}
            </div>
          </section>
        )}

        {session.status === 'teachback' && (
          <section className="workspace-pattern min-h-[calc(100vh-76px)] p-4 sm:p-6 lg:p-8">
            <div className="soft-card mx-auto max-w-4xl overflow-hidden p-4 sm:p-6 lg:p-10 w-full">
              <div className="mb-6 sm:mb-8 border-b border-[#e3e9f1] pb-4 sm:pb-6">
                <span className="rounded-full bg-[#eaf1ff] px-3 py-1.5 text-sm font-semibold text-[#1463ff]">Teach-Back</span>
                <h1 className="mt-4 text-2xl sm:text-3xl font-bold">Explain it in your own words</h1>
                <p className="mt-2 text-sm sm:text-base text-[#718096]">Show that the concept makes sense without relying on memorized language.</p>
              </div>
              <TeachBackPanel 
                currentConcept={currentConcept} 
                masteryScore={masteryScore} 
                confidenceScore={confidenceScore} 
                evaluation={teachBackEvaluation} 
                isLoading={submitTeachBackMutation.isPending} 
                onSubmitExplanation={(explanation) => submitTeachBackMutation.mutateAsync(explanation)} 
                onContinue={() => refetchSession()}
                onRetry={() => setTeachBackEvaluation(null)}
              />
            </div>
          </section>
        )}

        {session.status === 'completed' && (
          <CompletedSessionView 
            masteryEvents={masteryEvents || []}
            graph={graph}
            isLoading={masteryLoading}
            onNewSession={() => router.push('/new-session')}
          />
        )}

        {session.status === 'abandoned' && (
          <AbandonedSessionView
            session={session}
            masteryEvents={masteryEvents || []}
            graph={graph}
            isLoading={masteryLoading}
            onNewSession={() => router.push('/new-session')}
          />
        )}
      </FadeTransition>
    </AppShell>
  );
}

function AbandonedSessionView({
  session,
  masteryEvents,
  graph,
  isLoading,
  onNewSession,
}: {
  session: SessionResponse;
  masteryEvents: MasteryEvent[];
  graph?: PrerequisiteGraph;
  isLoading: boolean;
  onNewSession: () => void;
}) {
  // Calculate what was accomplished
  const conceptsWorkedOn = new Set(masteryEvents.map(e => e.concept_id)).size;
  const totalProgress = masteryEvents.reduce((sum, e) => sum + (e.new_score - e.old_score), 0);

  // Get concept names from graph
  const conceptNames = graph?.concepts.reduce((acc, c) => {
    acc[c.id] = c.name;
    return acc;
  }, {} as Record<string, string>) || {};

  return (
    <section className="workspace-pattern flex min-h-[calc(100vh-76px)] items-center justify-center p-6">
      <div className="soft-card w-full max-w-2xl p-10">
        <div className="text-center">
          <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#f0f2f5] text-3xl text-[#8792a5]">
            ⏸
          </span>
          <h1 className="mt-6 text-3xl font-bold">Session paused</h1>
          <p className="mx-auto mt-3 max-w-md text-[#718096]">
            This learning session was not completed. You can begin a fresh session whenever you are ready.
          </p>
        </div>

        {/* Show what was accomplished */}
        {!isLoading && masteryEvents.length > 0 && (
          <div className="mt-8 border-t border-[#e1e7ef] pt-8">
            <h2 className="mb-4 text-center text-lg font-semibold text-[#10213d]">
              Progress made before pausing
            </h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-[#dfe6ef] bg-[#f8fafc] p-4 text-center">
                <p className="text-2xl font-bold text-[#1463ff]">{conceptsWorkedOn}</p>
                <p className="mt-1 text-sm text-[#718096]">
                  Concept{conceptsWorkedOn !== 1 ? 's' : ''} explored
                </p>
              </div>
              <div className="rounded-xl border border-[#dfe6ef] bg-[#f8fafc] p-4 text-center">
                <p className="text-2xl font-bold text-[#20a572]">
                  {totalProgress > 0 ? `+${Math.round(totalProgress * 100)}%` : '0%'}
                </p>
                <p className="mt-1 text-sm text-[#718096]">Mastery gained</p>
              </div>
            </div>

            {/* List concepts worked on */}
            {conceptsWorkedOn > 0 && (
              <div className="mt-6">
                <p className="mb-3 text-sm font-medium text-[#718096]">Concepts you worked on:</p>
                <div className="space-y-2">
                  {Array.from(new Set(masteryEvents.map(e => e.concept_id))).slice(0, 5).map(conceptId => (
                    <div 
                      key={conceptId} 
                      className="flex items-center gap-3 rounded-lg border border-[#e8edf4] bg-white px-4 py-2"
                    >
                      <span className="h-2 w-2 rounded-full bg-[#1463ff]"></span>
                      <span className="text-sm text-[#10213d]">
                        {conceptNames[conceptId] || conceptId}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="mt-8 flex flex-col gap-3 text-center">
          {/* Note: Resume functionality would require backend support to restore session state */}
          <button
            type="button"
            onClick={onNewSession}
            className="rounded-xl bg-[#1463ff] px-6 py-3 font-semibold text-white hover:bg-[#0d4fc7] transition-colors"
          >
            Start a new session
          </button>
          <p className="text-sm text-[#8792a5]">
            Note: Resuming paused sessions is not currently available
          </p>
        </div>
      </div>
    </section>
  );
}

function CompletedSessionView({ 
  masteryEvents, 
  graph, 
  isLoading,
  onNewSession 
}: { 
  masteryEvents: MasteryEvent[]; 
  graph?: PrerequisiteGraph; 
  isLoading: boolean;
  onNewSession: () => void;
}) {
  // Calculate mastery achievements
  const conceptsLearned = new Set(masteryEvents.map(e => e.concept_id)).size;
  const totalScoreGain = masteryEvents.reduce((sum, e) => sum + (e.new_score - e.old_score), 0);
  const averageConfidence = masteryEvents.length > 0
    ? masteryEvents.reduce((sum, e) => sum + e.new_confidence, 0) / masteryEvents.length
    : 0;

  // Get concept names from graph
  const conceptNames = graph?.concepts.reduce((acc, c) => {
    acc[c.id] = c.name;
    return acc;
  }, {} as Record<string, string>) || {};

  // Group events by concept
  const eventsByConcept = masteryEvents.reduce((acc, event) => {
    if (!acc[event.concept_id]) {
      acc[event.concept_id] = [];
    }
    acc[event.concept_id].push(event);
    return acc;
  }, {} as Record<string, MasteryEvent[]>);

  // Get final mastery for each concept
  const conceptMasteryFinal = Object.entries(eventsByConcept).map(([conceptId, events]) => {
    const latestEvent = events[events.length - 1];
    return {
      conceptId,
      name: conceptNames[conceptId] || conceptId,
      finalScore: latestEvent.new_score,
      finalConfidence: latestEvent.new_confidence,
      improvement: latestEvent.new_score - events[0].old_score,
    };
  }).sort((a, b) => b.finalScore - a.finalScore);

  return (
    <section className="workspace-pattern min-h-[calc(100vh-76px)] p-4 sm:p-6 overflow-x-hidden w-full">
      <div className="mx-auto max-w-4xl w-full">
        {/* Celebration Card */}
        <div className="soft-card p-6 sm:p-10 text-center w-full overflow-hidden">
          <span className="mx-auto flex h-14 w-14 sm:h-16 sm:w-16 items-center justify-center rounded-full bg-[#e2f7ef] text-2xl sm:text-3xl text-[#20a572]">
            ✓
          </span>
          <h1 className="mt-4 sm:mt-6 text-2xl sm:text-3xl font-bold">Learning complete!</h1>
          <p className="mx-auto mt-3 max-w-md text-sm sm:text-base text-[#718096] px-4">
            You&apos;ve worked through the root knowledge gap and verified your understanding.
          </p>

          {isLoading ? (
            <div className="mt-8 flex justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#9dbaff] border-t-[#1463ff]"></div>
            </div>
          ) : (
            <>
              {/* Mastery Achievements */}
              {masteryEvents.length > 0 && (
                <div className="mt-8 grid gap-4 sm:grid-cols-3 w-full">
                  <div className="rounded-xl border border-[#dfe6ef] bg-[#f8fafc] p-4">
                    <p className="text-2xl font-bold text-[#1463ff]">{conceptsLearned}</p>
                    <p className="mt-1 text-sm text-[#718096]">Concepts learned</p>
                  </div>
                  <div className="rounded-xl border border-[#dfe6ef] bg-[#f8fafc] p-4">
                    <p className="text-2xl font-bold text-[#20a572]">
                      +{Math.round(totalScoreGain * 100)}%
                    </p>
                    <p className="mt-1 text-sm text-[#718096]">Total mastery gain</p>
                  </div>
                  <div className="rounded-xl border border-[#dfe6ef] bg-[#f8fafc] p-4">
                    <p className="text-2xl font-bold text-[#e8a12d]">
                      {Math.round(averageConfidence * 100)}%
                    </p>
                    <p className="mt-1 text-sm text-[#718096]">Avg. confidence</p>
                  </div>
                </div>
              )}

              {/* Concept Progress Details */}
              {conceptMasteryFinal.length > 0 && (
                <div className="mt-8 text-left w-full overflow-hidden">
                  <h2 className="mb-4 text-lg sm:text-xl font-bold">Your Progress</h2>
                  <div className="space-y-3 w-full">
                    {conceptMasteryFinal.map(({ conceptId, name, finalScore, finalConfidence, improvement }) => (
                      <div 
                        key={conceptId} 
                        className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 rounded-xl border border-[#dfe6ef] bg-white p-4 w-full overflow-hidden"
                      >
                        <div className="flex-1 min-w-0 w-full">
                          <p className="font-semibold text-[#10213d] break-words">{name}</p>
                          <div className="mt-2 flex flex-wrap items-center gap-3 sm:gap-4 text-sm text-[#718096]">
                            <span className="whitespace-nowrap">Mastery: {Math.round(finalScore * 100)}%</span>
                            <span className="whitespace-nowrap">Confidence: {Math.round(finalConfidence * 100)}%</span>
                            {improvement > 0 && (
                              <span className="text-[#20a572] whitespace-nowrap">
                                +{Math.round(improvement * 100)}%
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex-shrink-0">
                          {finalScore >= 0.8 ? (
                            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#e2f7ef] text-[#20a572]">
                              ✓
                            </span>
                          ) : finalScore >= 0.5 ? (
                            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#fff6e7] text-[#e8a12d]">
                              ◐
                            </span>
                          ) : (
                            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#f0f2f5] text-[#8792a5]">
                              ○
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Actions */}
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center w-full">
            <button
              type="button"
              onClick={onNewSession}
              className="w-full sm:w-auto rounded-xl bg-[#1463ff] px-6 py-3 font-semibold text-white hover:bg-[#0d4fc7] transition-colors"
            >
              Start a new session
            </button>
            {/* Session history placeholder - as per design missing backend capability note */}
            <button
              type="button"
              disabled
              className="w-full sm:w-auto rounded-xl border border-[#dfe6ef] bg-white px-6 py-3 font-semibold text-[#8792a5] opacity-50 cursor-not-allowed"
              title="Session history coming soon"
            >
              Review session history
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

function AnalyzingView({ topic, onCancel }: { topic: string; onCancel: () => void }) {
  const steps = [
    ['Understanding your topic', `Parsed your description of ${topic}`],
    ['Identifying the target concept', 'Locating the goal in the domain graph'],
    ['Building prerequisite relationships', 'Connecting the concepts you need first…'],
    ['Preparing your diagnostic assessment', 'Waiting for the knowledge map'],
  ];

  return (
    <section className="workspace-pattern flex min-h-[calc(100vh-76px)] flex-col items-center justify-center px-4 sm:px-5 py-8 sm:py-12 w-full overflow-hidden">
      <div className="soft-card w-full max-w-[670px] p-5 sm:p-7 lg:p-10">
        <div className="text-center">
          <span className="mx-auto flex h-14 w-14 sm:h-16 sm:w-16 items-center justify-center rounded-full border-2 border-[#9dbaff] bg-[#f1f6ff] text-xl sm:text-2xl text-[#1463ff]">⌘</span>
          <h1 className="mt-4 sm:mt-6 text-2xl sm:text-3xl font-bold">Analyzing your topic</h1>
          <p className="mt-2 text-base sm:text-lg text-[#718096]">Building your prerequisite knowledge map</p>
        </div>
        <ol className="mt-8 sm:mt-10 space-y-5 sm:space-y-6">
          {steps.map(([title, detail], index) => {
            const complete = index < 2;
            const active = index === 2;
            return (
              <li key={title} className="relative flex gap-3 sm:gap-4">
                {index < steps.length - 1 && <span className="absolute left-[18px] top-9 h-10 w-px bg-[#dbe4ef]" />}
                <span className={`relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 ${complete ? 'border-[#20a572] bg-[#20a572] text-white' : active ? 'animate-pulse border-[#1463ff] bg-white text-[#1463ff]' : 'border-[#dbe4ef] bg-white text-[#a7b2c2]'}`}>{complete ? '✓' : active ? '◔' : '○'}</span>
                <div className="min-w-0 flex-1">
                  <p className={`font-semibold text-sm sm:text-base ${active ? 'text-[#1463ff]' : complete ? 'text-[#10213d]' : 'text-[#718096]'}`}>{title}</p>
                  <p className="mt-0.5 text-xs sm:text-sm text-[#8792a5] break-words">{detail}</p>
                </div>
              </li>
            );
          })}
        </ol>
        <div className="mt-7 sm:mt-9 border-t border-[#e1e7ef] pt-5 sm:pt-7 text-center">
          <p className="text-base sm:text-lg font-semibold">Mapping what you need to know first…</p>
          <p className="mt-2 text-sm text-[#718096]">◷ This usually takes about a minute</p>
        </div>
      </div>
      <button type="button" onClick={onCancel} className="mt-6 sm:mt-7 text-sm font-medium text-[#718096] hover:text-[#10213d]">× &nbsp;Cancel and return home</button>
    </section>
  );
}

function GraphPanel({ graph, isLoading, error, onRetry, topic }: { graph?: PrerequisiteGraph; isLoading: boolean; error: Error | null; onRetry: () => void; topic: string }) {
  return (
    <KnowledgeMapCard
      graph={graph}
      isLoading={isLoading}
      error={error}
      topic={topic}
      onRetry={onRetry}
    />
  );
}

function RootGapView({ rootGap, graph, isLoading, onContinue }: { rootGap: RootGapResult | null; graph?: PrerequisiteGraph; isLoading: boolean; onContinue: () => void }) {
  const path = graph?.concepts.slice(0, 4) || [];
  return (
    <section className="min-h-[calc(100vh-76px)] px-4 py-6 sm:px-6 sm:py-10 w-full overflow-x-hidden">
      <div className="mx-auto max-w-5xl text-center w-full">
        <span className="rounded-full bg-[#ddf4ea] px-4 py-2 text-sm font-semibold text-[#18986b]">✓ Diagnosis complete</span>
        <h1 className="mt-6 text-3xl sm:text-4xl font-bold tracking-tight">We found the foundational gap</h1>
        <p className="mx-auto mt-3 max-w-2xl text-base sm:text-lg text-[#718096] px-4">Pinpointing the real starting point means the rest can click into place much faster.</p>
      </div>
      <div className="mx-auto mt-8 sm:mt-10 max-w-5xl w-full">
        <RootGapCard rootGap={rootGap} isLoading={isLoading} onFixGap={onContinue} />
        {rootGap && (
          <div className="soft-card mt-6 sm:mt-7 p-4 sm:p-7 lg:p-9 w-full overflow-hidden">
            <h2 className="text-lg sm:text-xl font-bold"><span className="mr-2 text-[#1463ff]">⌕</span>Evidence used to identify the gap</h2>
            <div className="mt-5 grid gap-4 sm:grid-cols-2 w-full">
              {rootGap.root_gap.reasons.slice(0, 4).map((reason, index) => <div key={reason} className="rounded-xl border border-[#dfe6ef] bg-[#f8fafc] p-4 break-words"><p className="font-semibold text-[#10213d]">Signal {index + 1}</p><p className="mt-1 text-sm leading-6 text-[#718096]">{reason}</p></div>)}
            </div>
            {path.length > 0 && <p className="mt-6 text-sm text-[#718096] break-words">Learning path: {path.map((concept) => concept.name).join(' → ')}</p>}
          </div>
        )}
      </div>
    </section>
  );
}

function LearningPath({ graph, rootGap }: { graph?: PrerequisiteGraph; rootGap: RootGapResult | null }) {
  const concepts = graph?.concepts.slice(0, 5) || [];
  return (
    <div className="space-y-4 sm:space-y-6 w-full overflow-hidden">
      <div className="soft-card p-4 sm:p-6 w-full">
        <h2 className="text-lg sm:text-xl font-bold">Learning Path</h2>
        <p className="mt-2 text-sm text-[#718096]">Root gap → target concept</p>
        <ol className="mt-6 space-y-4 sm:space-y-5">
          {concepts.map((concept, index) => {
            const isGap = concept.id === rootGap?.root_gap.concept_id;
            return <li key={concept.id} className="flex gap-3"><span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 ${concept.status === 'mastered' ? 'border-[#20a572] bg-[#20a572] text-white' : isGap ? 'border-[#1463ff] bg-[#1463ff] text-white' : 'border-[#e8a12d] bg-[#fff6e7] text-[#e8a12d]'}`}>{concept.status === 'mastered' ? '✓' : isGap ? '▷' : index + 1}</span><div className="min-w-0 flex-1"><p className={`font-semibold truncate ${isGap ? 'text-[#1463ff]' : ''}`}>{concept.name}</p><p className="text-sm capitalize text-[#718096]">{isGap ? 'Current · Root gap' : concept.status}</p></div></li>;
          })}
        </ol>
      </div>
      <div className="soft-card p-4 sm:p-6 w-full"><h3 className="font-bold text-sm sm:text-base">Mastery legend</h3><div className="mt-4 space-y-3 text-sm text-[#718096]"><p><span className="mr-2 text-[#20a572]">●</span>Mastered</p><p><span className="mr-2 text-[#1463ff]">●</span>Current root gap</p><p><span className="mr-2 text-[#e8a12d]">●</span>Learning</p><p><span className="mr-2 text-[#a7b2c2]">○</span>Not reached</p></div></div>
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
  retryLabel = 'Try Again',
  error,
}: { 
  title: string; 
  message: string; 
  onRetry: () => void;
  retryLabel?: string;
  error?: Error | APIError | null;
}) {
  // Determine error type and provide specific guidance
  const getErrorGuidance = () => {
    if (error instanceof APIError) {
      // Network errors (no status or connection issues)
      if (!error.status || error.message.toLowerCase().includes('network') || error.message.toLowerCase().includes('fetch')) {
        return {
          type: 'network',
          guidance: 'Please check your internet connection and try again.',
          icon: (
            <svg className="w-16 h-16 text-[#e8a12d] mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
            </svg>
          ),
        };
      }
      
      // Server errors (5xx)
      if (error.status >= 500) {
        return {
          type: 'server',
          guidance: 'The server encountered an error. Please try again in a few moments.',
          icon: (
            <svg className="w-16 h-16 text-[#ef4444] mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
            </svg>
          ),
        };
      }
      
      // Client errors (4xx)
      if (error.status >= 400 && error.status < 500) {
        return {
          type: 'client',
          guidance: error.message || 'There was a problem with the request.',
          icon: (
            <svg className="w-16 h-16 text-[#ef4444] mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          ),
        };
      }
    }
    
    // Generic error
    return {
      type: 'generic',
      guidance: 'An unexpected error occurred. Please try again.',
      icon: (
        <svg className="w-16 h-16 text-[#ef4444] mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
    };
  };

  const errorGuidance = getErrorGuidance();

  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-[#f4f7fb]">
      <div className="soft-card max-w-md p-10 text-center">
        <div className="mb-6">
          {errorGuidance.icon}
        </div>
        <h2 className="text-2xl font-bold text-[#10213d] mb-2">{title}</h2>
        <p className="text-[#718096] mb-4">{message}</p>
        
        {/* Specific error guidance */}
        <div className="rounded-xl bg-[#f8fafc] border border-[#dfe6ef] p-4 mb-6">
          <p className="text-sm text-[#718096]">{errorGuidance.guidance}</p>
        </div>

        {/* Request ID if available */}
        {error instanceof APIError && error.requestId && (
          <p className="text-xs text-[#8792a5] mb-6">
            Request ID: {error.requestId}
          </p>
        )}

        <button
          onClick={onRetry}
          className="w-full rounded-xl bg-[#1463ff] px-6 py-3 font-semibold text-white hover:bg-[#0d4fc7] transition-colors"
        >
          {retryLabel}
        </button>
      </div>
    </div>
  );
}
