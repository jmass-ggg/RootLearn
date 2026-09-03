import React from 'react';
import { Header, SessionState } from './Header';
import { Sidebar } from './Sidebar';
import { useRouter } from 'next/navigation';

/**
 * SessionShell Component
 * 
 * The main layout wrapper for all session screens.
 * Provides consistent header, sidebar, and workspace background across the application.
 * Highlights the active section in the sidebar based on current session phase.
 * 
 * @example
 * // Diagnostic phase
 * <SessionShell
 *   sessionId={session.id}
 *   userId={session.user_id}
 *   currentPhase="diagnosing"
 *   topic="Understanding Recursion"
 * >
 *   <DiagnosticScreen />
 * </SessionShell>
 * 
 * @example
 * // Tutoring phase
 * <SessionShell
 *   sessionId={session.id}
 *   userId={session.user_id}
 *   currentPhase="tutoring"
 *   topic={session.target_concept}
 * >
 *   <TutorPanel />
 * </SessionShell>
 * 
 * @example
 * // Without active session (landing page)
 * <SessionShell
 *   sessionId=""
 *   userId=""
 *   currentPhase="analyzing"
 *   topic=""
 * >
 *   <LandingContent />
 * </SessionShell>
 */
export interface SessionShellProps {
  /**
   * Current session ID
   * 
   * Pass empty string if no active session (e.g., landing page)
   * Used for navigation and session-specific actions
   */
  sessionId: string;
  
  /**
   * Current user ID
   * 
   * Pass empty string if not authenticated
   * Preserved throughout navigation
   */
  userId: string;
  
  /**
   * Current phase of the learning session
   * 
   * Determines which sidebar section is highlighted
   * Maps to workflow stages:
   * - `analyzing`: Overview section
   * - `diagnosing`: Diagnosis section  
   * - `tutoring`: AI Tutor section
   * - `teachback`: Teach-Back section
   * - `completed`: Progress section
   */
  currentPhase: SessionState;
  
  /**
   * Current topic or learning goal
   * 
   * Displayed in header for context
   * Can be user's original prompt or identified target concept
   * 
   * @example "Understanding recursion in programming"
   * @example "Functions and Variables"
   */
  topic: string;
  
  /**
   * Main content area
   * 
   * All session screens render inside this layout
   */
  children: React.ReactNode;
}

/**
 * SessionShell Component Implementation
 * 
 * Composes Header, Sidebar, and main workspace into a cohesive layout.
 * Conditionally shows sidebar only when in an active session.
 * Applies subtle concept-network background pattern to workspace.
 * Handles responsive layout adjustments for mobile and desktop.
 * 
 * Layout structure:
 * ```
 * ┌─────────────────────────────────┐
 * │          Header                 │
 * ├──────────┬─────────────────────┤
 * │ Sidebar  │  Main Workspace     │
 * │          │  (children)         │
 * │          │                     │
 * └──────────┴─────────────────────┘
 * ```
 */
export const SessionShell: React.FC<SessionShellProps> = ({
  sessionId,
  userId,
  currentPhase,
  topic,
  children,
}) => {
  const router = useRouter();

  const handleNewSession = () => {
    router.push('/new-session');
  };

  const handleNavigate = (section: string) => {
    const query = new URLSearchParams({ user_id: userId });

    if (section === 'knowledge-map' || section === 'progress') {
      query.set('section', section);
    }

    if (section === 'teach-back') {
      router.push(`/session/${sessionId}/teachback?${query.toString()}`);
      return;
    }

    router.push(`/session/${sessionId}?${query.toString()}`);
  };

  // Check if we're in an active session (has sessionId)
  const hasActiveSession = sessionId && sessionId.length > 0;

  return (
    <div className="h-screen flex flex-col overflow-hidden w-full">
      {/* Header */}
      <Header
        sessionId={hasActiveSession ? sessionId : undefined}
        currentPhase={hasActiveSession ? currentPhase : undefined}
        topic={hasActiveSession ? topic : undefined}
        onNewSession={handleNewSession}
      />

      {/* Main content area with optional sidebar */}
      <div className="flex-1 flex overflow-hidden w-full min-w-0">
        {/* Sidebar - only show if in active session */}
        {hasActiveSession && (
          <Sidebar
            currentPhase={currentPhase}
            sessionId={sessionId}
            onNavigate={handleNavigate}
          />
        )}

        {/* Main workspace */}
        <main className="flex-1 overflow-auto bg-bg-workspace w-full min-w-0">
          {/* Concept network background pattern */}
          <div 
            className="min-h-full w-full"
            style={{
              backgroundImage: `
                radial-gradient(circle at 20% 30%, rgba(20, 99, 255, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(210, 233, 13, 0.02) 0%, transparent 50%),
                radial-gradient(circle at 50% 50%, rgba(5, 47, 78, 0.02) 0%, transparent 70%)
              `,
            }}
          >
            {/* Content container with padding */}
            <div className="container mx-auto px-4 py-6 md:px-6 md:py-8 max-w-[1800px] w-full">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};
