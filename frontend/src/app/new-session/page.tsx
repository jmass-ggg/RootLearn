"use client";

import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { v4 as uuidv4 } from "uuid";
import { SessionShell } from "@/components/layout/SessionShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";

const topics = ["Recursion", "Calculus", "Probability", "SQL Joins", "Neural Networks"];

export default function NewSessionPage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  
  const mutation = useMutation({
    mutationFn: (value: string) => api.sessions.create({ user_id: uuidv4(), prompt: value }),
    onSuccess: (session) => router.push(`/session/${session.id}?user_id=${session.user_id}`),
  });
  
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (prompt.trim()) mutation.mutate(prompt.trim());
  };

  // For new session page, we don't have a session yet, so we provide placeholder values
  // SessionShell will handle the case where sessionId is empty
  return (
    <SessionShell
      sessionId=""
      userId=""
      currentPhase="analyzing"
      topic="New Session"
    >
      <div className="flex min-h-[calc(100vh-200px)] items-center justify-center">
        <Card variant="default" padding="xl" className="w-full max-w-[760px]">
          <form onSubmit={submit} aria-label="New diagnostic session">
            {/* Icon */}
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-xl text-brand-blue">
              ⌕
            </div>
            
            {/* Heading */}
            <h1 className="mt-4 text-3xl font-bold tracking-tight text-text-heading">
              What are you trying to understand?
            </h1>
            
            {/* Explanatory text */}
            <p className="mt-3 max-w-2xl leading-7 text-text-body">
              Describe the concept that confuses you. RootLearn will map the prerequisites and find the foundational gap behind your confusion.
            </p>
            
            {/* Textarea */}
            <label htmlFor="session-prompt" className="sr-only">
              Describe what you are trying to understand
            </label>
            <textarea
              id="session-prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              rows={7}
              maxLength={2000}
              placeholder="For example: I understand loops, but recursion still confuses me…"
              className="mt-7 w-full resize-none rounded-2xl border border-transparent bg-bg-workspace p-5 text-lg placeholder:text-text-muted focus:border-brand-blue focus:bg-bg-card focus:outline-none"
              autoFocus
            />
            
            {/* Topic suggestions */}
            <div className="mt-5">
              <p className="text-sm font-medium text-text-body">Suggested topics</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {topics.map((topic) => (
                  <button
                    key={topic}
                    type="button"
                    onClick={() => setPrompt(topic)}
                    className="rounded-full bg-blue-50 px-4 py-2 text-sm font-semibold text-brand-blue hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2 transition-colors"
                    tabIndex={0}
                  >
                    {topic}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Error message */}
            {mutation.isError && (
              <p role="alert" className="mt-5 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {mutation.error instanceof Error ? mutation.error.message : "We couldn't start the diagnosis. Please try again."}
              </p>
            )}
            
            {/* Privacy reassurance and submit button */}
            <div className="mt-7 flex flex-col-reverse items-stretch justify-between gap-4 sm:flex-row sm:items-center">
              <p className="text-sm text-text-body">
                <span className="mr-2">🔒</span>Your answers stay private
              </p>
              <Button
                type="submit"
                variant="primary"
                size="lg"
                isDisabled={!prompt.trim()}
                isLoading={mutation.isPending}
              >
                {mutation.isPending ? "Mapping your topic…" : "Diagnose my understanding"}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </SessionShell>
  );
}
