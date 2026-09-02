'use client';

import { useState, useEffect, useRef } from 'react';
import { TutorMessage, TutorMessageResponse } from '@/types/tutor';

interface TutorPanelProps {
  sessionId: string;
  userId: string;
  messages: TutorMessage[];
  currentConcept: {
    id: string;
    name: string;
  } | null;
  masteryScore: number;
  confidenceScore: number;
  isLoading: boolean;
  onSendMessage: (message: string) => Promise<TutorMessageResponse>;
  onExplainBack: () => Promise<void>;
}

/**
 * TutorPanel component
 * Displays Socratic tutoring conversation with progressive hint levels
 * Requirements: 9.2, 9.6
 */
export default function TutorPanel({
  sessionId,
  userId,
  messages,
  currentConcept,
  masteryScore,
  confidenceScore,
  isLoading,
  onSendMessage,
  onExplainBack,
}: TutorPanelProps) {
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || isSending) {
      return;
    }

    const messageToSend = input.trim();
    setInput('');
    setIsSending(true);

    try {
      await onSendMessage(messageToSend);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Restore input on error
      setInput(messageToSend);
    } finally {
      setIsSending(false);
    }
  };

  const handleExplainBack = async () => {
    setIsTransitioning(true);
    try {
      await onExplainBack();
    } catch (error) {
      console.error('Failed to transition to teach-back:', error);
    } finally {
      setIsTransitioning(false);
    }
  };

  const getMasteryColor = (score: number): string => {
    if (score >= 0.85) return 'text-green-600';
    if (score >= 0.70) return 'text-lime-600';
    if (score >= 0.40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getMasteryBgColor = (score: number): string => {
    if (score >= 0.85) return 'bg-green-500';
    if (score >= 0.70) return 'bg-lime-500';
    if (score >= 0.40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getHintLevelLabel = (level: number | null): string => {
    if (level === null) return '';
    const labels = ['Question', 'Small Hint', 'Stronger Hint', 'Example', 'Explanation'];
    return labels[level] || '';
  };

  // Loading State
  if (isLoading && messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-64" role="status" aria-live="polite">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-3" aria-hidden="true"></div>
          <p className="text-gray-600 text-sm">Loading tutoring session...</p>
          <span className="sr-only">Loading tutoring session, please wait</span>
        </div>
      </div>
    );
  }

  // Empty State
  if (!currentConcept) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500 p-6" role="status">
        <svg
          className="w-16 h-16 text-gray-400 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        <p className="text-center">No tutoring session active</p>
        <p className="text-sm text-gray-400 mt-2">Tutoring will begin after diagnosis</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-md">
      {/* Header with concept name and mastery bar - Responsive */}
      <div className="p-3 sm:p-4 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
          <div className="flex-1 min-w-0">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 truncate">
              Learning: {currentConcept.name}
            </h3>
            <p className="text-xs sm:text-sm text-gray-500">
              Socratic tutoring in progress
            </p>
          </div>
          <div className="text-left sm:text-right flex-shrink-0">
            <div className={`text-xl sm:text-2xl font-bold ${getMasteryColor(masteryScore)}`} aria-label={`Mastery: ${Math.round(masteryScore * 100)} percent`}>
              {Math.round(masteryScore * 100)}%
            </div>
            <div className="text-xs text-gray-500">
              Confidence: {Math.round(confidenceScore * 100)}%
            </div>
          </div>
        </div>

        {/* Mastery progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-2" role="progressbar" aria-valuenow={masteryScore * 100} aria-valuemin={0} aria-valuemax={100} aria-label="Mastery progress">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${getMasteryBgColor(
              masteryScore
            )}`}
            style={{ width: `${masteryScore * 100}%` }}
          />
        </div>
      </div>

      {/* Chat messages - Responsive */}
      <div 
        className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4"
        role="log"
        aria-live="polite"
        aria-label="Tutoring conversation"
      >
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p className="text-sm sm:text-base text-center px-4">Start the conversation by asking a question...</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[85%] sm:max-w-[80%] rounded-lg px-3 sm:px-4 py-2 sm:py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
                role="article"
                aria-label={`${message.role === 'user' ? 'Your message' : 'Tutor message'}`}
              >
                {message.role === 'assistant' && message.hint_level !== null && (
                  <div className="text-xs font-medium mb-1 opacity-75">
                    {getHintLevelLabel(message.hint_level)}
                  </div>
                )}
                <div className="whitespace-pre-wrap break-words text-sm sm:text-base">
                  {message.content}
                </div>
                <div
                  className={`text-xs mt-1 ${
                    message.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}
                >
                  {new Date(message.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area - Responsive */}
      <div className="p-3 sm:p-4 border-t border-gray-200 space-y-3">
        <form onSubmit={handleSubmit} className="flex gap-2" aria-label="Send tutor message">
          <input
            type="text"
            name="tutor-message"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your response or question..."
            className="flex-1 px-3 sm:px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm sm:text-base transition-shadow"
            disabled={isSending}
            aria-label="Your message"
          />
          <button
            type="submit"
            disabled={isSending || !input.trim()}
            className="px-4 sm:px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors text-sm sm:text-base flex-shrink-0"
            aria-label={isSending ? 'Sending message, please wait' : 'Send message'}
          >
            {isSending ? (
              <span className="flex items-center">
                <svg
                  className="animate-spin h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                <span className="sr-only">Sending</span>
              </span>
            ) : (
              'Send'
            )}
          </button>
        </form>

        {/* Explain it back button - Responsive */}
        <button
          onClick={handleExplainBack}
          disabled={isSending || isTransitioning}
          className="w-full px-3 sm:px-4 py-2 sm:py-3 bg-gradient-to-r from-purple-500 to-indigo-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-indigo-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg text-sm sm:text-base"
          aria-label="Request to explain concept back"
        >
          {isTransitioning ? (
            <span className="flex items-center justify-center gap-2">
              <svg
                className="animate-spin h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Transitioning...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <span aria-hidden="true">✓</span>
              <span>I'm ready to explain it back</span>
            </span>
          )}
        </button>
        <p className="text-xs text-center text-gray-500 px-2">
          When you feel you understand, explain the concept in your own words
        </p>
      </div>
    </div>
  );
}
