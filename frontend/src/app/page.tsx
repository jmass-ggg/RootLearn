'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { v4 as uuidv4 } from 'uuid';

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const router = useRouter();

  const createSessionMutation = useMutation({
    mutationFn: async (userPrompt: string) => {
      // For MVP, generate a temporary user ID
      // In production, this would come from authentication
      const userId = uuidv4();
      
      return api.sessions.create({
        user_id: userId,
        prompt: userPrompt,
      });
    },
    onSuccess: (session) => {
      // Navigate to the session page
      router.push(`/session/${session.id}?user_id=${session.user_id}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (prompt.trim()) {
      createSessionMutation.mutate(prompt.trim());
    }
  };

  const handleRetry = () => {
    if (prompt.trim()) {
      createSessionMutation.reset();
      createSessionMutation.mutate(prompt.trim());
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 sm:p-6 md:p-8 bg-gradient-to-b from-blue-50 to-white">
      <div className="w-full max-w-2xl">
        {/* Header - Responsive */}
        <div className="text-center mb-8 sm:mb-12">
          <h1 
            className="text-3xl sm:text-4xl md:text-5xl font-bold mb-3 sm:mb-4 text-gray-900"
            role="heading"
            aria-level={1}
          >
            RootLearn
          </h1>
          <p className="text-lg sm:text-xl text-gray-600 mb-2">
            AI-powered knowledge debugger
          </p>
          <p className="text-sm sm:text-base text-gray-500 px-4">
            Identify and fix your knowledge gaps with intelligent tutoring
          </p>
        </div>

        {/* Main Form Card - Responsive */}
        <div className="bg-white rounded-lg shadow-lg p-6 sm:p-8">
          <form onSubmit={handleSubmit} className="space-y-6" aria-label="Create learning session form">
            <div>
              <label
                htmlFor="prompt"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                What are you struggling with?
                <span className="sr-only"> (required)</span>
              </label>
              <textarea
                id="prompt"
                name="learning-prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., I don't understand recursion in programming..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-900 transition-shadow"
                rows={6}
                disabled={createSessionMutation.isPending}
                required
                aria-required="true"
                aria-describedby={createSessionMutation.isError ? 'error-message' : undefined}
                autoFocus
              />
            </div>

            {/* Error State with Retry */}
            {createSessionMutation.isError && (
              <div 
                id="error-message"
                className="p-4 bg-red-50 border border-red-200 rounded-lg"
                role="alert"
                aria-live="polite"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-red-800 mb-1">
                      {createSessionMutation.error instanceof Error
                        ? createSessionMutation.error.message
                        : 'Failed to create session. Please try again.'}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleRetry}
                    className="text-sm font-medium text-red-700 hover:text-red-900 underline flex-shrink-0"
                    aria-label="Retry creating session"
                  >
                    Retry
                  </button>
                </div>
              </div>
            )}

            {/* Submit Button with Loading State */}
            <button
              type="submit"
              disabled={!prompt.trim() || createSessionMutation.isPending}
              className="w-full bg-blue-600 text-white font-medium py-3 px-6 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02] active:scale-[0.98]"
              aria-label={createSessionMutation.isPending ? 'Creating session, please wait' : 'Start diagnosis'}
            >
              {createSessionMutation.isPending ? (
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
                  Creating session...
                </span>
              ) : (
                'Diagnose my understanding'
              )}
            </button>
          </form>

          {/* Information Text - Responsive */}
          <div className="mt-6 text-center text-xs sm:text-sm text-gray-500 px-2">
            <p>
              RootLearn will analyze what you&apos;re struggling with, identify
              prerequisite gaps, and guide you through targeted learning.
            </p>
          </div>
        </div>

        {/* Keyboard Navigation Hint */}
        <div className="mt-6 text-center text-xs text-gray-400 hidden sm:block">
          <p>Press Tab to navigate • Press Enter to submit</p>
        </div>
      </div>
    </main>
  );
}

