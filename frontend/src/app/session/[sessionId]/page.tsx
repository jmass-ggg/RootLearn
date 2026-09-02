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
import AppShell, { WorkspaceSection } from '@/components/AppShell';
import type { PrerequisiteGraph, RootGapResult } from '@/types';
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

      {session.status === 'analyzing' && <AnalyzingView topic={session.normalized_topic || session.original_prompt} onCancel={() => router.push('/')} />}

      {session.status === 'diagnosing' && (
        <section className="mx-auto grid min-h-[calc(100vh-76px)] max-w-[1540px] gap-6 p-4 sm:p-7 xl:grid-cols-[1.55fr_1fr]">
          {graphPanel}
          <div className="soft-card min-h-[680px] overflow-hidden p-6 sm:p-8">
            <DiagnosticPanel question={currentQuestion || null} evaluation={lastEvaluation} isLoading={questionLoading} onSubmitAnswer={async (answer) => { await submitAnswerMutation.mutateAsync(answer); }} />
          </div>
        </section>
      )}

      {session.status === 'tutoring' && !showTutor && (
        <RootGapView rootGap={rootGap || null} graph={graph} isLoading={rootGapLoading} onContinue={() => setShowTutor(true)} />
      )}

      {session.status === 'tutoring' && showTutor && (
        <section className="mx-auto grid min-h-[calc(100vh-76px)] max-w-[1540px] gap-6 p-4 sm:p-7 xl:grid-cols-[340px_1fr]">
          <LearningPath graph={graph} rootGap={rootGap || null} />
          <div className="soft-card min-h-[760px] overflow-hidden">
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
        <section className="workspace-pattern min-h-[calc(100vh-76px)] p-4 sm:p-8">
          <div className="soft-card mx-auto max-w-4xl overflow-hidden p-6 sm:p-10">
            <div className="mb-8 border-b border-[#e3e9f1] pb-6">
              <span className="rounded-full bg-[#eaf1ff] px-3 py-1.5 text-sm font-semibold text-[#1463ff]">Teach-Back</span>
              <h1 className="mt-4 text-3xl font-bold">Explain it in your own words</h1>
              <p className="mt-2 text-[#718096]">Show that the concept makes sense without relying on memorized language.</p>
            </div>
            <TeachBackPanel currentConcept={currentConcept} masteryScore={masteryScore} confidenceScore={confidenceScore} evaluation={teachBackEvaluation} isLoading={submitTeachBackMutation.isPending} onSubmitExplanation={(explanation) => submitTeachBackMutation.mutateAsync(explanation)} onContinue={() => refetchSession()} />
          </div>
        </section>
      )}

      {(session.status === 'completed' || session.status === 'abandoned') && (
        <section className="workspace-pattern flex min-h-[calc(100vh-76px)] items-center justify-center p-6">
          <div className="soft-card w-full max-w-xl p-10 text-center">
            <span className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full text-3xl ${session.status === 'completed' ? 'bg-[#e2f7ef] text-[#20a572]' : 'bg-[#f0f2f5] text-[#8792a5]'}`}>{session.status === 'completed' ? '✓' : '×'}</span>
            <h1 className="mt-6 text-3xl font-bold">{session.status === 'completed' ? 'Learning complete!' : 'Session paused'}</h1>
            <p className="mx-auto mt-3 max-w-md text-[#718096]">{session.status === 'completed' ? "You've worked through the root knowledge gap and verified your understanding." : 'This learning session was not completed. You can begin a fresh session whenever you are ready.'}</p>
            <button type="button" onClick={() => router.push('/new-session')} className="mt-8 rounded-xl bg-[#1463ff] px-6 py-3 font-semibold text-white">Start a new session</button>
          </div>
        </section>
      )}
    </AppShell>
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
    <section className="workspace-pattern flex min-h-[calc(100vh-76px)] flex-col items-center justify-center px-5 py-12">
      <div className="soft-card w-full max-w-[670px] p-7 sm:p-10">
        <div className="text-center">
          <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-full border-2 border-[#9dbaff] bg-[#f1f6ff] text-2xl text-[#1463ff]">⌘</span>
          <h1 className="mt-6 text-3xl font-bold">Analyzing your topic</h1>
          <p className="mt-2 text-lg text-[#718096]">Building your prerequisite knowledge map</p>
        </div>
        <ol className="mt-10 space-y-6">
          {steps.map(([title, detail], index) => {
            const complete = index < 2;
            const active = index === 2;
            return (
              <li key={title} className="relative flex gap-4">
                {index < steps.length - 1 && <span className="absolute left-[18px] top-9 h-10 w-px bg-[#dbe4ef]" />}
                <span className={`relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 ${complete ? 'border-[#20a572] bg-[#20a572] text-white' : active ? 'animate-pulse border-[#1463ff] bg-white text-[#1463ff]' : 'border-[#dbe4ef] bg-white text-[#a7b2c2]'}`}>{complete ? '✓' : active ? '◔' : '○'}</span>
                <div>
                  <p className={`font-semibold ${active ? 'text-[#1463ff]' : complete ? 'text-[#10213d]' : 'text-[#718096]'}`}>{title}</p>
                  <p className="mt-0.5 text-sm text-[#8a96a9]">{detail}</p>
                </div>
              </li>
            );
          })}
        </ol>
        <div className="mt-9 border-t border-[#e1e7ef] pt-7 text-center">
          <p className="text-lg font-semibold">Mapping what you need to know first…</p>
          <p className="mt-2 text-sm text-[#718096]">◷ This usually takes about a minute</p>
        </div>
      </div>
      <button type="button" onClick={onCancel} className="mt-7 text-sm font-medium text-[#718096] hover:text-[#10213d]">× &nbsp;Cancel and return home</button>
    </section>
  );
}

function GraphPanel({ graph, isLoading, error, onRetry, topic }: { graph?: PrerequisiteGraph; isLoading: boolean; error: Error | null; onRetry: () => void; topic: string }) {
  return (
    <div className="soft-card min-h-[680px] overflow-hidden">
      <div className="border-b border-[#e1e7ef] p-6 sm:p-8">
        <div className="flex items-start justify-between gap-4">
          <div><h1 className="text-2xl font-bold"><span className="mr-3 text-[#1463ff]">⌘</span>Knowledge Map</h1><p className="mt-2 text-[#718096]">Prerequisites for {topic}</p></div>
          <div className="flex gap-2" aria-label="Graph controls"><span className="rounded-lg border border-[#dce5ef] px-3 py-2">⊕</span><span className="rounded-lg border border-[#dce5ef] px-3 py-2">⊖</span><span className="rounded-lg border border-[#dce5ef] px-3 py-2">↶</span></div>
        </div>
      </div>
      <div className="flex flex-wrap gap-x-5 gap-y-2 border-b border-[#e1e7ef] px-6 py-4 text-sm text-[#718096] sm:px-8">
        {[['#9aa6b7','Unknown'],['#dc4b50','Weak'],['#eca633','Learning'],['#6ee7ad','Understood'],['#20a572','Mastered'],['#d2e90d','Root gap']].map(([color,label]) => <span key={label} className="flex items-center gap-2"><i className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />{label}</span>)}
      </div>
      <div className="h-[540px]">
        {isLoading ? <LoadingDisplay message="Building your knowledge map…" compact /> : error ? (
          <div className="flex h-full flex-col items-center justify-center p-6 text-center"><p className="text-[#718096]">{error instanceof APIError && error.status === 404 ? 'Knowledge map is being generated…' : 'Failed to load the knowledge map.'}</p>{!(error instanceof APIError && error.status === 404) && <button type="button" onClick={onRetry} className="mt-4 font-semibold text-[#1463ff]">Retry</button>}</div>
        ) : graph ? <KnowledgeGraph graph={graph} /> : <div className="flex h-full items-center justify-center text-[#718096]">No knowledge map available yet</div>}
      </div>
    </div>
  );
}

function RootGapView({ rootGap, graph, isLoading, onContinue }: { rootGap: RootGapResult | null; graph?: PrerequisiteGraph; isLoading: boolean; onContinue: () => void }) {
  const path = graph?.concepts.slice(0, 4) || [];
  return (
    <section className="min-h-[calc(100vh-76px)] px-4 py-10 sm:px-8">
      <div className="mx-auto max-w-5xl text-center">
        <span className="rounded-full bg-[#ddf4ea] px-4 py-2 text-sm font-semibold text-[#18986b]">✓ Diagnosis complete</span>
        <h1 className="mt-6 text-4xl font-bold tracking-tight">We found the foundational gap</h1>
        <p className="mx-auto mt-3 max-w-2xl text-lg text-[#718096]">Pinpointing the real starting point means the rest can click into place much faster.</p>
      </div>
      <div className="mx-auto mt-10 max-w-5xl">
        <RootGapCard rootGap={rootGap} isLoading={isLoading} onFixGap={onContinue} />
        {rootGap && (
          <div className="soft-card mt-7 p-7 sm:p-9">
            <h2 className="text-xl font-bold"><span className="mr-2 text-[#1463ff]">⌕</span>Evidence used to identify the gap</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              {rootGap.root_gap.reasons.slice(0, 4).map((reason, index) => <div key={reason} className="rounded-xl border border-[#dfe6ef] bg-[#f8fafc] p-4"><p className="font-semibold text-[#10213d]">Signal {index + 1}</p><p className="mt-1 text-sm leading-6 text-[#718096]">{reason}</p></div>)}
            </div>
            {path.length > 0 && <p className="mt-6 text-sm text-[#718096]">Learning path: {path.map((concept) => concept.name).join(' → ')}</p>}
          </div>
        )}
      </div>
    </section>
  );
}

function LearningPath({ graph, rootGap }: { graph?: PrerequisiteGraph; rootGap: RootGapResult | null }) {
  const concepts = graph?.concepts.slice(0, 5) || [];
  return (
    <div className="space-y-6">
      <div className="soft-card p-6">
        <h2 className="text-xl font-bold">Learning Path</h2>
        <p className="mt-2 text-sm text-[#718096]">Root gap → target concept</p>
        <ol className="mt-6 space-y-5">
          {concepts.map((concept, index) => {
            const isGap = concept.id === rootGap?.root_gap.concept_id;
            return <li key={concept.id} className="flex gap-3"><span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 ${concept.status === 'mastered' ? 'border-[#20a572] bg-[#20a572] text-white' : isGap ? 'border-[#1463ff] bg-[#1463ff] text-white' : 'border-[#e8a12d] bg-[#fff6e7] text-[#e8a12d]'}`}>{concept.status === 'mastered' ? '✓' : isGap ? '▷' : index + 1}</span><div><p className={`font-semibold ${isGap ? 'text-[#1463ff]' : ''}`}>{concept.name}</p><p className="text-sm capitalize text-[#718096]">{isGap ? 'Current · Root gap' : concept.status}</p></div></li>;
          })}
        </ol>
      </div>
      <div className="soft-card p-6"><h3 className="font-bold">Mastery legend</h3><div className="mt-4 space-y-3 text-sm text-[#718096]"><p><span className="mr-2 text-[#20a572]">●</span>Mastered</p><p><span className="mr-2 text-[#1463ff]">●</span>Current root gap</p><p><span className="mr-2 text-[#e8a12d]">●</span>Learning</p><p><span className="mr-2 text-[#a7b2c2]">○</span>Not reached</p></div></div>
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
