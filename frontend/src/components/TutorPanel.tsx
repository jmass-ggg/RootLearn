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

  if (isLoading && messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!currentConcept) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <p>No tutoring session active</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-md">
      {/* Header with concept name and mastery bar */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Learning: {currentConcept.name}
            </h3>
            <p className="text-sm text-gray-500">
              Socratic tutoring in progress
            </p>
          </div>
          <div className="text-right">
            <div className={`text-2xl font-bold ${getMasteryColor(masteryScore)}`}>
              {Math.round(masteryScore * 100)}%
            </div>
            <div className="text-xs text-gray-500">
              Confidence: {Math.round(confidenceScore * 100)}%
            </div>
          </div>
        </div>

        {/* Mastery progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${getMasteryBgColor(
              masteryScore
            )}`}
            style={{ width: `${masteryScore * 100}%` }}
          />
        </div>
      </div>

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>Start the conversation by asking a question...</p>
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
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                {message.role === 'assistant' && message.hint_level !== null && (
                  <div className="text-xs font-medium mb-1 opacity-75">
                    {getHintLevelLabel(message.hint_level)}
                  </div>
                )}
                <div className="whitespace-pre-wrap break-words">
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

      {/* Input area */}
      <div className="p-4 border-t border-gray-200 space-y-3">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your response or question..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isSending}
          />
          <button
            type="submit"
            disabled={isSending || !input.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isSending ? (
              <span className="flex items-center">
                <svg
                  className="animate-spin h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
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
              </span>
            ) : (
              'Send'
            )}
          </button>
        </form>

        {/* Explain it back button */}
        <button
          onClick={handleExplainBack}
          disabled={isSending || isTransitioning}
          className="w-full px-4 py-3 bg-gradient-to-r from-purple-500 to-indigo-500 text-white rounded-lg font-semibold hover:from-purple-600 hover:to-indigo-600 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
        >
          {isTransitioning ? (
            <span className="flex items-center justify-center gap-2">
              <svg
                className="animate-spin h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
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
            "✓ I'm ready to explain it back"
          )}
        </button>
        <p className="text-xs text-center text-gray-500">
          When you feel you understand, explain the concept in your own words
        </p>
      </div>
    </div>
  );
}
