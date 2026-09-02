import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import type { SessionState } from './Header';

export interface SidebarProps {
  currentPhase: SessionState;
  sessionId: string;
  onNavigate?: (section: string) => void;
}

interface SidebarSection {
  id: string;
  label: string;
  icon: React.ReactNode;
  phase?: SessionState | SessionState[];
  isAccessible: boolean;
  href?: string;
}

// Icon components for each section
const OverviewIcon = () => (
  <svg className="w-5 h-5" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
    <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
  </svg>
);

const KnowledgeMapIcon = () => (
  <svg className="w-5 h-5" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
    <path d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
  </svg>
);

const DiagnosisIcon = () => (
  <svg className="w-5 h-5" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
    <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
  </svg>
);

const RootGapIcon = () => (
  <svg className="w-5 h-5" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
    <path d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
);

const TutorIcon = () => (
  <svg className="w-5 h-5" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
    <path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
  </svg>
);

const TeachBackIcon = () => (
  <svg className="w-5 h-5" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
    <path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
  </svg>
);

const ProgressIcon = () => (
  <svg className="w-5 h-5" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
    <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const HistoryIcon = () => (
  <svg className="w-5 h-5" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
    <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const phaseExplanations: Record<SessionState, { title: string; description: string }> = {
  analyzing: {
    title: 'Building your knowledge map',
    description: 'We\'re mapping the prerequisites for what you want to learn.',
  },
  diagnosing: {
    title: 'Finding your knowledge gaps',
    description: 'Answer questions to help us identify where you need support.',
  },
  tutoring: {
    title: 'Guided learning',
    description: 'Work through Socratic dialogue to build your understanding.',
  },
  teachback: {
    title: 'Verify your learning',
    description: 'Explain the concept back to confirm you\'ve mastered it.',
  },
  completed: {
    title: 'Session complete',
    description: 'Great work! You\'ve completed this learning session.',
  },
  abandoned: {
    title: 'Session paused',
    description: 'This session was stopped. You can start a new one anytime.',
  },
};

export const Sidebar: React.FC<SidebarProps> = ({
  currentPhase,
  sessionId,
  onNavigate,
}) => {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const sections: SidebarSection[] = [
    {
      id: 'overview',
      label: 'Overview',
      icon: <OverviewIcon />,
      phase: ['analyzing', 'diagnosing', 'tutoring', 'teachback', 'completed'],
      isAccessible: true,
      href: `/sessions/${sessionId}`,
    },
    {
      id: 'knowledge-map',
      label: 'Knowledge Map',
      icon: <KnowledgeMapIcon />,
      phase: ['diagnosing', 'tutoring', 'teachback', 'completed'],
      isAccessible: true,
      href: `/sessions/${sessionId}/graph`,
    },
    {
      id: 'diagnosis',
      label: 'Diagnosis',
      icon: <DiagnosisIcon />,
      phase: 'diagnosing',
      isAccessible: currentPhase === 'diagnosing',
      href: currentPhase === 'diagnosing' ? `/sessions/${sessionId}` : undefined,
    },
    {
      id: 'root-gap',
      label: 'Root Gap',
      icon: <RootGapIcon />,
      phase: ['tutoring', 'teachback', 'completed'],
      isAccessible: ['tutoring', 'teachback', 'completed'].includes(currentPhase),
      href: ['tutoring', 'teachback', 'completed'].includes(currentPhase) 
        ? `/sessions/${sessionId}/root-gap` 
        : undefined,
    },
    {
      id: 'ai-tutor',
      label: 'AI Tutor',
      icon: <TutorIcon />,
      phase: 'tutoring',
      isAccessible: currentPhase === 'tutoring',
      href: currentPhase === 'tutoring' ? `/sessions/${sessionId}/tutor` : undefined,
    },
    {
      id: 'teach-back',
      label: 'Teach-Back',
      icon: <TeachBackIcon />,
      phase: 'teachback',
      isAccessible: currentPhase === 'teachback',
      href: currentPhase === 'teachback' ? `/sessions/${sessionId}/teachback` : undefined,
    },
    {
      id: 'progress',
      label: 'Progress',
      icon: <ProgressIcon />,
      isAccessible: false, // Not implemented yet
    },
    {
      id: 'session-history',
      label: 'Session History',
      icon: <HistoryIcon />,
      isAccessible: false, // Not implemented yet
    },
  ];

  const isActive = (section: SidebarSection): boolean => {
    if (Array.isArray(section.phase)) {
      return section.phase.includes(currentPhase);
    }
    return section.phase === currentPhase;
  };

  const handleSectionClick = (section: SidebarSection) => {
    if (section.isAccessible && section.href) {
      onNavigate?.(section.id);
      setIsMobileOpen(false);
    }
  };

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Navigation sections */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {sections.map((section) => {
          const active = isActive(section);
          const accessible = section.isAccessible;
          
          return (
            <button
              key={section.id}
              onClick={() => handleSectionClick(section)}
              disabled={!accessible}
              aria-disabled={!accessible}
              aria-current={active ? 'page' : undefined}
              className={`
                w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                transition-colors
                focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2
                focus-visible:ring-2 focus-visible:ring-brand-blue
                ${active 
                  ? 'bg-brand-blue text-text-inverse' 
                  : accessible
                    ? 'text-text-body hover:bg-gray-100'
                    : 'text-text-muted cursor-not-allowed opacity-60'
                }
              `}
            >
              <span className={active ? 'text-text-inverse' : accessible ? 'text-brand-blue' : 'text-text-muted'}>
                {section.icon}
              </span>
              <span>{section.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Contextual stage explanation card */}
      <div className="p-3 border-t border-border-default">
        <Card variant="default" padding="md">
          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-text-heading">
              {phaseExplanations[currentPhase].title}
            </h3>
            <p className="text-xs text-text-body leading-relaxed">
              {phaseExplanations[currentPhase].description}
            </p>
          </div>
        </Card>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="lg:hidden fixed bottom-4 right-4 z-40 w-12 h-12 bg-brand-blue text-text-inverse rounded-full shadow-lg flex items-center justify-center"
        aria-label="Toggle navigation menu"
      >
        {isMobileOpen ? (
          <svg className="w-6 h-6" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
            <path d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        )}
      </button>

      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-30"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Desktop sidebar */}
      <aside className="hidden lg:flex w-64 bg-bg-card border-r border-border-default flex-col h-full">
        {sidebarContent}
      </aside>

      {/* Mobile sidebar */}
      <aside
        className={`
          lg:hidden fixed inset-y-0 left-0 z-40 w-64 bg-bg-card border-r border-border-default
          transform transition-transform duration-300 ease-in-out
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {sidebarContent}
      </aside>
    </>
  );
};
