import React from 'react';
import { Button } from '@/components/ui/Button';

export type SessionState = 
  | 'analyzing' 
  | 'diagnosing' 
  | 'tutoring' 
  | 'teachback' 
  | 'completed' 
  | 'abandoned';

export interface HeaderProps {
  sessionId?: string;
  currentPhase?: SessionState;
  topic?: string;
  onNewSession: () => void;
}

const phaseLabels: Record<SessionState, string> = {
  analyzing: 'Analyzing',
  diagnosing: 'Diagnosing',
  tutoring: 'Tutoring',
  teachback: 'Teach-Back',
  completed: 'Completed',
  abandoned: 'Abandoned',
};

const phaseColors: Record<SessionState, string> = {
  analyzing: 'bg-blue-100 text-blue-800',
  diagnosing: 'bg-amber-100 text-amber-800',
  tutoring: 'bg-purple-100 text-purple-800',
  teachback: 'bg-green-100 text-green-800',
  completed: 'bg-green-200 text-green-900',
  abandoned: 'bg-gray-200 text-gray-700',
};

export const Header: React.FC<HeaderProps> = ({
  sessionId,
  currentPhase,
  topic,
  onNewSession,
}) => {
  return (
    <header className="sticky top-0 z-50 w-full bg-bg-card border-b border-border-default shadow-sm">
      <div className="flex items-center justify-between px-4 md:px-6 py-3 md:py-4">
        {/* Left section: Logo and session context */}
        <div className="flex items-center gap-4 md:gap-6 min-w-0 flex-1">
          {/* Logo/Identity */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="w-8 h-8 bg-brand-navy rounded-lg flex items-center justify-center">
              <span className="text-brand-lime font-bold text-lg">R</span>
            </div>
            <span className="hidden sm:inline text-text-heading font-semibold text-lg">
              RootLearn
            </span>
          </div>

          {/* Session context - only show if in session */}
          {sessionId && (
            <div className="flex items-center gap-2 md:gap-3 min-w-0 flex-1">
              {/* Phase badge */}
              {currentPhase && (
                <span 
                  className={`px-2 py-1 rounded-md text-xs md:text-sm font-medium whitespace-nowrap ${phaseColors[currentPhase]}`}
                >
                  {phaseLabels[currentPhase]}
                </span>
              )}

              {/* Topic - truncate on small screens */}
              {topic && (
                <div className="hidden md:flex items-center gap-2 min-w-0">
                  <span className="text-text-muted">•</span>
                  <span className="text-text-body text-sm truncate" title={topic}>
                    {topic}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right section: Actions and user */}
        <div className="flex items-center gap-2 md:gap-4 flex-shrink-0">
          {/* New session button */}
          <Button
            variant="secondary"
            size="sm"
            onClick={onNewSession}
            className="whitespace-nowrap"
          >
            <span className="hidden sm:inline">New session</span>
            <span className="sm:hidden">New</span>
          </Button>

          {/* User placeholder icon */}
          <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
            <svg
              className="w-5 h-5 text-gray-600"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Mobile topic display - show below header on small screens */}
      {sessionId && topic && (
        <div className="md:hidden px-4 pb-3 border-t border-border-default pt-2">
          <span className="text-text-body text-sm truncate block" title={topic}>
            {topic}
          </span>
        </div>
      )}
    </header>
  );
};
