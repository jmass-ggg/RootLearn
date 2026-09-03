'use client';

import { useState, useEffect, useRef } from 'react';
import { TutorMessage, TutorMessageResponse } from '@/types/tutor';
import { Button } from './ui/Button';
import { smoothScrollToBottom } from '@/lib/scroll-utils';

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
 * Requirements: 8.5, 8.6, 8.7
 * 
 * Features:
 * - Chronological message history
 * - Differentiated user vs AI message styling
 * - Auto-scroll to latest message
 * - Hint level display in UI
 * - Error recovery without losing history
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
  const [sendError, setSendError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  // Requirements: 8.6 - auto-scroll behavior, 15.5 - smooth scroll
  useEffect(() => {
    if (messagesContainerRef.current) {
      smoothScrollToBottom(messagesContainerRef.current);
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || isSending) {
      return;
    }

    const messageToSend = input.trim();
    setInput('');
    setSendError(null);
    setIsSending(true);

    try {
      await onSendMessage(messageToSend);
      // Focus input after successful send for quick follow-up
      inputRef.current?.focus();
    } catch (error) {
      // Requirements: 8.7 - error recovery without losing history
      console.error('Failed to send message:', error);
      setSendError('Failed to send message. Please try again.');
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
      setSendError('Failed to transition to teach-back. Please try again.');
    } finally {
      setIsTransitioning(false);
    }
  };

  const getHintLevelLabel = (level: number | null): string => {
    // Requirements: 8.6 - hint levels visible in UI
    if (level === null) return '';
    const labels = ['Question', 'Small Hint', 'Stronger Hint', 'Example', 'Explanation'];
    return labels[level] || '';
  };

  // Loading State
  if (isLoading && messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-96" role="status" aria-live="polite">
        <div className="text-center">
          <div
            className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-blue mx-auto mb-3"
            aria-hidden="true"
          ></div>
          <p className="text-text-body text-sm">Loading tutoring session...</p>
          <span className="sr-only">Loading tutoring session, please wait</span>
        </div>
      </div>
    );
  }

  // Empty State - no active concept
  if (!currentConcept) {
    return (
      <div
        className="flex flex-col items-center justify-center h-96 text-text-muted p-6"
        role="status"
      >
        <svg
          className="w-16 h-16 text-mastery-unknown mb-4"
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
        <p className="text-center font-medium">No tutoring session active</p>
        <p className="text-sm text-text-muted mt-2">Tutoring will begin after diagnosis</p>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-[760px] flex-col">
      {/* Chat messages area - Requirements: 8.5, 8.6, 8.10, 8.11 */}
      <div
        ref={messagesContainerRef}
        className="min-h-[500px] flex-1 space-y-4 overflow-y-auto bg-bg-workspace p-5 sm:p-8 overscroll-contain"
        role="log"
        aria-live="polite"
        aria-label="Tutoring conversation"
        style={{
          // Requirements: 8.11 - ensure scrolling works on mobile touch devices
          WebkitOverflowScrolling: 'touch',
        }}
      >
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-text-body">
            <div className="max-w-md text-center">
              <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-xl text-brand-blue">
                ○
              </span>
              <p className="mt-4 px-4 text-base">
                Start by sharing how you currently think about {currentConcept.name}. The
                tutor will guide you with questions.
              </p>
            </div>
          </div>
        ) : (
          // Requirements: 8.5 - display message history in chronological order
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[85%] sm:max-w-[80%] rounded-lg px-3 sm:px-4 py-2 sm:py-3 ${
                  // Requirements: 8.5 - style user messages vs AI messages differently
                  message.role === 'user'
                    ? 'bg-brand-blue text-white'
                    : 'border border-border bg-white text-text-heading'
                }`}
                role="article"
                aria-label={`${message.role === 'user' ? 'Your message' : 'Tutor message'}`}
              >
                {/* Requirements: 8.6 - preserve hint levels in UI */}
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
                    message.role === 'user' ? 'text-blue-100' : 'text-text-muted'
                  }`}
                >
                  {new Date(message.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} aria-hidden="true" />
      </div>

      {/* Input area - Requirements: 8.10, 8.11, 14.6 */}
      <div className="space-y-3 border-t border-border bg-white p-5 sm:p-8 sticky bottom-0">
        {/* Error message - Requirements: 8.7 */}
        {sendError && (
          <div
            className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-800"
            role="alert"
          >
            {sendError}
          </div>
        )}

        {/* Prompt suggestions - Requirements: 8.8, 8.9 */}
        <div className="flex flex-wrap gap-2">
          {[
            'Can you give me a hint?',
            'Show me another example',
            "I'm still confused",
          ].map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => {
                // Requirements: 8.9 - populate composer WITHOUT auto-submitting
                setInput(suggestion);
                inputRef.current?.focus();
              }}
              // Requirements: 14.6 - keyboard accessible
              className="rounded-full border border-border bg-white px-3 py-1.5 text-sm text-text-body hover:border-brand-blue hover:text-brand-blue hover:bg-blue-50 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-opacity-50"
              disabled={isSending}
              tabIndex={0}
            >
              {suggestion}
            </button>
          ))}
        </div>

        {/* Message composer - Requirements: 8.10 - keyboard accessible */}
        <form
          onSubmit={handleSubmit}
          className="flex gap-2 rounded-2xl border border-border bg-white p-2 focus-within:ring-2 focus-within:ring-brand-blue focus-within:ring-opacity-20"
          aria-label="Send tutor message"
        >
          <input
            ref={inputRef}
            type="text"
            name="tutor-message"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your response or question..."
            // Requirements: 8.11 - keep input visible on mobile (prevent keyboard from hiding it)
            className="min-w-0 flex-1 border-0 bg-transparent px-3 py-2 text-sm outline-none sm:text-base placeholder:text-text-muted"
            disabled={isSending}
            aria-label="Your message"
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="sentences"
          />
          <button
            type="submit"
            disabled={isSending || !input.trim()}
            className="h-11 w-11 flex-shrink-0 rounded-xl bg-brand-blue font-medium text-white transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:bg-mastery-unknown disabled:opacity-50 flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2"
            aria-label={isSending ? 'Sending message, please wait' : 'Send message'}
          >
            {isSending ? (
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
            ) : (
              '➤'
            )}
          </button>
        </form>

        {/* Explain it back button - Requirements: 8.12 */}
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center pt-2 border-t border-border">
          <Button
            variant="primary"
            size="lg"
            onClick={handleExplainBack}
            isLoading={isTransitioning}
            isDisabled={isSending || isTransitioning}
            className="w-full sm:w-auto bg-brand-navy hover:bg-opacity-90"
          >
            <span className="flex items-center justify-center gap-2">
              <span aria-hidden="true">✓</span>
              <span>I&apos;m ready to explain it back</span>
            </span>
          </Button>
          <p className="text-xs text-center sm:text-left text-text-muted px-2 sm:flex-1">
            When you feel you understand, explain the concept in your own words
          </p>
        </div>
      </div>
    </div>
  );
}

