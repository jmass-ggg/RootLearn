"use client";

import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { v4 as uuidv4 } from "uuid";
import { api } from "@/lib/api";
import { BrandMark } from "@/components/AppShell";

const suggestedTopics = ["Recursion", "Calculus", "Probability", "SQL Joins", "Neural Networks"];

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const router = useRouter();
  const createSessionMutation = useMutation({
    mutationFn: (userPrompt: string) => api.sessions.create({ user_id: uuidv4(), prompt: userPrompt }),
    onSuccess: (session) => router.push(`/session/${session.id}?user_id=${session.user_id}`),
  });
  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = prompt.trim();
    if (trimmed) createSessionMutation.mutate(trimmed);
  };
  const scrollToStart = () => document.getElementById("start")?.scrollIntoView({ behavior: "smooth" });

  return (
    <main className="min-h-screen bg-[#f4f7fb] text-[#10213d]">
      <section className="network-pattern relative min-h-[760px] bg-[#052f4e] text-white">
        <header className="mx-auto flex h-20 max-w-[1440px] items-center justify-between px-6 lg:px-12">
          <BrandMark />
          <nav className="hidden items-center gap-12 text-sm font-medium text-white/65 md:flex" aria-label="Main navigation">
            <a href="#how-it-works" className="transition hover:text-white">How it works</a>
            <a href="#features" className="transition hover:text-white">Features</a>
            <a href="#about" className="transition hover:text-white">About</a>
          </nav>
          <button type="button" onClick={() => router.push('/new-session')} className="rounded-xl bg-[#1463ff] px-5 py-2.5 text-sm font-semibold transition hover:bg-[#397cff]">Try RootLearn</button>
        </header>
        <div className="mx-auto flex max-w-5xl flex-col items-center px-6 pb-44 pt-32 text-center sm:pt-36">
          <span className="mb-7 rounded-full border border-white/20 bg-white/5 px-4 py-2 text-sm text-white/70"><span className="mr-2 text-[#d2e90d]">✣</span>AI-powered knowledge debugger</span>
          <h1 className="max-w-4xl text-5xl font-bold leading-[1.05] tracking-[-0.04em] sm:text-6xl lg:text-[72px]">Find the gap behind the confusion.</h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-[#b2c1d0] sm:text-xl">RootLearn maps prerequisite concepts, diagnoses hidden knowledge gaps, and guides you toward real understanding.</p>
          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row">
            <button type="button" onClick={scrollToStart} className="rounded-xl bg-[#d2e90d] px-6 py-3.5 font-bold text-[#10213d] shadow-lg shadow-black/10 transition hover:-translate-y-0.5 hover:bg-[#e0f22c]">Start learning <span className="ml-2">→</span></button>
            <button type="button" onClick={() => { setPrompt("I understand loops, but recursion still confuses me."); scrollToStart(); }} className="rounded-xl px-5 py-3.5 font-semibold text-white/90 transition hover:bg-white/5"><span className="mr-2">▷</span>Explore a demo</button>
          </div>
          <p className="mt-6 text-sm text-white/50"><span className="mr-2 text-[#d2e90d]">✓</span>No account required</p>
        </div>
        <div className="absolute inset-x-0 bottom-0 h-20 overflow-hidden" aria-hidden="true"><div className="absolute -bottom-12 -left-[5%] h-24 w-[110%] rounded-[50%_50%_0_0] bg-[#f4f7fb]" /></div>
      </section>

      <section id="how-it-works" className="mx-auto max-w-6xl scroll-mt-12 px-6 pb-24 pt-20">
        <div className="text-center">
          <p className="text-sm font-bold uppercase tracking-[0.12em] text-[#1463ff]">How it works</p>
          <h2 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">Three steps to real understanding</h2>
          <p className="mt-3 text-lg text-[#718096]">A calm, guided path from confusion to clarity.</p>
        </div>
        <div id="features" className="mt-14 grid gap-6 md:grid-cols-3">
          {[
            ["01", "□", "Describe what you do not understand", "Tell RootLearn the topic that confuses you, in your own words. No prior structure needed."],
            ["02", "⌘", "Discover your root knowledge gap", "We build a prerequisite map and diagnose the foundational concept holding you back."],
            ["03", "▤", "Learn through questions and teach-back", "Socratic tutoring guides you with questions, then verifies mastery through teach-back."],
          ].map(([number, icon, title, text]) => (
            <article key={number} className="soft-card relative min-h-[278px] p-8">
              <span className="absolute right-7 top-7 text-3xl font-bold text-[#e5eaf2]">{number}</span>
              <span className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl border border-[#dce5f2] bg-[#f7f9fc] text-xl text-[#1463ff]">{icon}</span>
              <h3 className="max-w-[250px] text-xl font-bold leading-7">{title}</h3>
              <p className="mt-4 leading-7 text-[#718096]">{text}</p>
            </article>
          ))}
        </div>

        <form id="start" onSubmit={handleSubmit} className="soft-card mx-auto mt-16 max-w-3xl scroll-mt-8 p-6 sm:p-8" aria-label="Create learning session">
          <label htmlFor="prompt" className="block text-center font-semibold">Ready to begin? Tell us what confuses you.</label>
          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <input id="prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="I understand loops, but recursion still confuses me..." className="min-h-14 flex-1 rounded-xl border border-transparent bg-[#f4f7fb] px-4 placeholder:text-[#8a94a6] focus:border-[#1463ff] focus:bg-white" disabled={createSessionMutation.isPending} maxLength={2000} required />
            <button type="submit" disabled={!prompt.trim() || createSessionMutation.isPending} className="min-h-14 rounded-xl bg-[#1463ff] px-6 font-semibold text-white transition hover:bg-[#0754e8] disabled:cursor-not-allowed disabled:bg-[#b8c5d8]">{createSessionMutation.isPending ? "Starting…" : "Start learning →"}</button>
          </div>
          <div className="mt-4 flex flex-wrap justify-center gap-2">{suggestedTopics.map((topic) => <button key={topic} type="button" onClick={() => setPrompt(topic)} className="rounded-full bg-[#edf3ff] px-3 py-1.5 text-sm font-medium text-[#1463ff] hover:bg-[#dfeaff]">{topic}</button>)}</div>
          {createSessionMutation.isError && (
            <div role="alert" className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              <span>{createSessionMutation.error instanceof Error ? createSessionMutation.error.message : "Failed to create the session. Please try again."}</span>
              <button type="button" className="font-semibold underline" onClick={() => createSessionMutation.mutate(prompt.trim())}>Retry</button>
            </div>
          )}
        </form>
      </section>
      <footer id="about" className="border-t border-[#dfe6ef] bg-white px-6 py-8 text-center text-sm text-[#718096]">RootLearn turns confusion into a clear, testable learning path.</footer>
    </main>
  );
}
