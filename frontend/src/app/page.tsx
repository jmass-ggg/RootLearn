"use client";

import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { v4 as uuidv4 } from "uuid";
import { api } from "@/lib/api";
import type { SessionResponse } from "@/lib/api";
import { BrandMark } from "@/components/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useToast } from "@/lib/useToast";

const suggestedTopics = ["Recursion", "Calculus", "Probability", "SQL Joins", "Neural Networks"];

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const router = useRouter();
  const toast = useToast();
  const createSessionMutation = useMutation({
    mutationFn: (userPrompt: string) => api.sessions.create({ user_id: uuidv4(), prompt: userPrompt }),
    onSuccess: (session: SessionResponse) => {
      toast.success("Session created! Redirecting...");
      router.push(`/session/${session.id}?user_id=${session.user_id}`);
    },
    onError: (error: Error) => {
      toast.error(
        error instanceof Error 
          ? error.message 
          : "Failed to create session. Please try again."
      );
    },
  });
  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = prompt.trim();
    if (trimmed) createSessionMutation.mutate(trimmed);
  };
  const scrollToStart = () => document.getElementById("start")?.scrollIntoView({ behavior: "smooth" });

  return (
    <main className="min-h-screen bg-bg-workspace text-text-heading">
      {/* Hero Section */}
      <section className="network-pattern relative min-h-[760px] bg-brand-navy text-text-inverse">
        {/* Header Navigation */}
        <header className="mx-auto flex h-20 max-w-[1440px] items-center justify-between px-6 lg:px-12">
          <BrandMark />
          <nav className="hidden items-center gap-12 text-sm font-medium text-white/65 md:flex" aria-label="Main navigation">
            <a href="#how-it-works" className="transition hover:text-white">How it works</a>
            <a href="#features" className="transition hover:text-white">Features</a>
            <a href="#about" className="transition hover:text-white">About</a>
          </nav>
          <Button 
            variant="primary" 
            size="sm"
            onClick={scrollToStart}
            className="rounded-xl"
            aria-label="Try RootLearn - Start learning"
          >
            Try RootLearn
          </Button>
        </header>

        {/* Hero Content */}
        <div className="mx-auto flex max-w-5xl flex-col items-center px-6 pb-44 pt-32 text-center sm:pt-36">
          {/* Hero Badge */}
          <span className="mb-7 rounded-full border border-white/20 bg-white/5 px-4 py-2 text-sm text-white/70" role="status">
            <span className="mr-2 text-brand-lime" aria-hidden="true">✣</span>
            AI-powered knowledge debugger
          </span>

          {/* Headline */}
          <h1 className="max-w-4xl text-5xl font-bold leading-[1.05] tracking-[-0.04em] sm:text-6xl lg:text-[72px]">
            Find the gap behind the confusion.
          </h1>

          {/* Supporting Copy */}
          <p className="mt-7 max-w-2xl text-lg leading-8 text-[#b2c1d0] sm:text-xl">
            RootLearn maps prerequisite concepts, diagnoses hidden knowledge gaps, and guides you toward real understanding.
          </p>

          {/* CTA Buttons */}
          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row">
            <Button
              variant="lime"
              size="lg"
              onClick={scrollToStart}
              className="shadow-lg shadow-black/10 transition hover:-translate-y-0.5"
              aria-label="Start learning with RootLearn"
            >
              Start learning <span aria-hidden="true" className="ml-2">→</span>
            </Button>
            <button 
              type="button" 
              onClick={() => { 
                setPrompt("I understand loops, but recursion still confuses me."); 
                scrollToStart(); 
              }} 
              className="rounded-xl px-5 py-3.5 font-semibold text-white/90 transition hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-white/50"
              aria-label="Explore a demo with recursion example"
            >
              <span aria-hidden="true" className="mr-2">▷</span>Explore a demo
            </button>
          </div>

          {/* No Account Required Reassurance */}
          <p className="mt-6 text-sm text-white/50">
            <span className="mr-2 text-brand-lime" aria-hidden="true">✓</span>No account required
          </p>
        </div>

        {/* Soft Curved Wave Transition */}
        <div className="absolute inset-x-0 bottom-0 h-20 overflow-hidden" aria-hidden="true">
          <div className="absolute -bottom-12 -left-[5%] h-24 w-[110%] rounded-[50%_50%_0_0] bg-bg-workspace" />
        </div>
      </section>

      {/* Three Steps to Real Understanding Section */}
      <section id="how-it-works" className="mx-auto max-w-6xl scroll-mt-12 px-6 pb-24 pt-20">
        <div className="text-center">
          <p className="text-sm font-bold uppercase tracking-[0.12em] text-brand-blue">How it works</p>
          <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">Three steps to real understanding</h2>
          <p className="mt-3 text-lg text-text-body">A calm, guided path from confusion to clarity.</p>
        </div>

        {/* Three Steps Cards */}
        <div id="features" className="mt-14 grid gap-6 md:grid-cols-3" role="list">
          {[
            ["01", "□", "Describe what you don't understand", "Tell RootLearn the topic that confuses you, in your own words. No prior structure needed."],
            ["02", "⌘", "Discover your root knowledge gap", "We build a prerequisite map and diagnose the foundational concept holding you back."],
            ["03", "▤", "Learn through questions and teach-back", "Socratic tutoring guides you with questions, then verifies mastery through teach-back."],
          ].map(([number, icon, title, text]) => (
            <Card key={number} variant="elevated" padding="xl" className="relative min-h-[278px]" role="listitem">
              <span className="absolute right-7 top-7 text-3xl font-bold text-[#e5eaf2]" aria-hidden="true">{number}</span>
              <span className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl border border-[#dce5f2] bg-[#f7f9fc] text-xl text-brand-blue" aria-hidden="true">
                {icon}
              </span>
              <h3 className="max-w-[250px] text-xl font-bold leading-7">{title}</h3>
              <p className="mt-4 leading-7 text-text-body">{text}</p>
            </Card>
          ))}
        </div>

        {/* Quick-Start Form */}
        <Card 
          variant="elevated"
          padding="lg"
          className="mx-auto mt-16 max-w-3xl scroll-mt-8"
        >
          <form id="start" onSubmit={handleSubmit} aria-label="Create learning session">
            <label htmlFor="prompt" className="block text-center font-semibold">
              Ready to begin? Tell us what confuses you.
            </label>
            <div className="mt-5 flex flex-col gap-3 sm:flex-row">
              <input 
                id="prompt" 
                value={prompt} 
                onChange={(event) => setPrompt(event.target.value)} 
                placeholder="I understand loops, but recursion still confuses me..." 
                className="min-h-14 flex-1 rounded-xl border border-transparent bg-bg-workspace px-4 placeholder:text-text-muted focus:border-brand-blue focus:bg-bg-card focus:outline-none focus:ring-2 focus:ring-brand-blue/20" 
                disabled={createSessionMutation.isPending} 
                maxLength={2000} 
                required 
                aria-required="true"
                aria-invalid={createSessionMutation.isError ? 'true' : 'false'}
                aria-describedby={createSessionMutation.isError ? 'session-error' : undefined}
              />
              <Button
                type="submit"
                variant="primary"
                size="lg"
                isDisabled={!prompt.trim() || createSessionMutation.isPending}
                isLoading={createSessionMutation.isPending}
                className="min-h-14 rounded-xl"
                aria-label={createSessionMutation.isPending ? "Starting session..." : "Start learning session"}
              >
                {createSessionMutation.isPending ? "Starting…" : "Start learning →"}
              </Button>
            </div>

            {/* Topic Suggestions */}
            <div className="mt-4 flex flex-wrap justify-center gap-2" role="group" aria-label="Suggested topics">
              {suggestedTopics.map((topic) => (
                <button 
                  key={topic} 
                  type="button" 
                  onClick={() => setPrompt(topic)} 
                  className="rounded-full bg-[#edf3ff] px-3 py-1.5 text-sm font-medium text-brand-blue hover:bg-[#dfeaff] transition focus:outline-none focus:ring-2 focus:ring-brand-blue focus:ring-offset-2"
                  aria-label={`Use suggested topic: ${topic}`}
                >
                  {topic}
                </button>
              ))}
            </div>

            {/* Error State */}
            {createSessionMutation.isError && (
              <div id="session-error" role="alert" aria-live="assertive" className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                <span>
                  {createSessionMutation.error instanceof Error 
                    ? createSessionMutation.error.message 
                    : "Failed to create the session. Please try again."}
                </span>
                <button 
                  type="button" 
                  className="font-semibold underline focus:outline-none focus:ring-2 focus:ring-red-500" 
                  onClick={() => createSessionMutation.mutate(prompt.trim())}
                  aria-label="Retry creating session"
                >
                  Retry
                </button>
              </div>
            )}
          </form>
        </Card>
      </section>

      {/* Footer */}
      <footer id="about" className="border-t border-border-default bg-bg-card px-6 py-8 text-center text-sm text-text-body">
        <p>RootLearn turns confusion into a clear, testable learning path.</p>
      </footer>
    </main>
  );
}
