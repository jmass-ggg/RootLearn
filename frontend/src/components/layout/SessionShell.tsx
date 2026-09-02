import React from 'react';
import { Header, SessionState } from './Header';
import { Sidebar } from './Sidebar';
import { useRouter } from 'next/navigation';

export interface SessionShellProps {
  sessionId: string;
  userId: string;
  currentPhase: SessionState;
  topic: string;
  children: React.ReactNode;
}

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
    // Navigation is handled by the Sidebar component via href attributes
    // This callback can be used for additional logic if needed
    console.log('Navigating to section:', section);
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
