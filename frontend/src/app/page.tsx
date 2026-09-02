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

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gradient-to-b from-blue-50 to-white">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 text-gray-900">RootLearn</h1>
          <p className="text-xl text-gray-600 mb-2">AI-powered knowledge debugger</p>
          <p className="text-gray-500">
            Identify and fix your knowledge gaps with intelligent tutoring
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label
                htmlFor="prompt"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                What are you struggling with?
              </label>
              <textarea
                id="prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., I don't understand recursion in programming..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-900"
                rows={6}
                disabled={createSessionMutation.isPending}
                required
              />
            </div>

            {createSessionMutation.isError && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">
                  {createSessionMutation.error instanceof Error
                    ? createSessionMutation.error.message
                    : 'Failed to create session. Please try again.'}
                </p>
              </div>
            )}

            <button
              type="submit"
              disabled={!prompt.trim() || createSessionMutation.isPending}
              className="w-full bg-blue-600 text-white font-medium py-3 px-6 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {createSessionMutation.isPending
                ? 'Creating session...'
                : 'Diagnose my understanding'}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-500">
            <p>
              RootLearn will analyze what you&apos;re struggling with, identify
              prerequisite gaps, and guide you through targeted learning.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}

