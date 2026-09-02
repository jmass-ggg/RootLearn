"use client";

import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { v4 as uuidv4 } from "uuid";
import AppShell from "@/components/AppShell";
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

  return (
    <AppShell activeSection="overview" onNewSession={() => setPrompt("")}>
      <section className="workspace-pattern flex min-h-[calc(100vh-76px)] items-center justify-center p-4 sm:p-8">
        <form onSubmit={submit} className="soft-card w-full max-w-[760px] p-6 sm:p-10" aria-label="New diagnostic session">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#edf3ff] text-xl text-[#1463ff]">⌕</div>
          <p className="mt-4 text-sm font-bold uppercase tracking-[.1em] text-[#718096]">Diagnostic</p>
          <h1 className="mt-3 text-3xl font-bold tracking-tight">What are you trying to understand?</h1>
          <p className="mt-3 max-w-2xl leading-7 text-[#718096]">Describe the concept that confuses you. RootLearn will map the prerequisites and find the foundational gap behind your confusion.</p>
          <label htmlFor="session-prompt" className="sr-only">Describe what you are trying to understand</label>
          <textarea id="session-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={7} maxLength={2000} placeholder="For example: I understand loops, but recursion still confuses me…" className="mt-7 w-full resize-none rounded-2xl border border-transparent bg-[#f4f7fb] p-5 text-lg placeholder:text-[#8e98a9] focus:border-[#1463ff] focus:bg-white" autoFocus />
          <div className="mt-5">
            <p className="text-sm font-medium text-[#718096]">Suggested topics</p>
            <div className="mt-3 flex flex-wrap gap-2">{topics.map((topic) => <button key={topic} type="button" onClick={() => setPrompt(topic)} className="rounded-full bg-[#edf3ff] px-4 py-2 text-sm font-semibold text-[#1463ff] hover:bg-[#dfeaff]">{topic}</button>)}</div>
          </div>
          {mutation.isError && <p role="alert" className="mt-5 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{mutation.error instanceof Error ? mutation.error.message : "We couldn't start the diagnosis. Please try again."}</p>}
          <div className="mt-7 flex flex-col-reverse items-stretch justify-between gap-4 sm:flex-row sm:items-center">
            <p className="text-sm text-[#718096]"><span className="mr-2">♙</span>Your answers stay private</p>
            <button type="submit" disabled={!prompt.trim() || mutation.isPending} className="rounded-xl bg-[#1463ff] px-6 py-3.5 font-semibold text-white transition hover:bg-[#0754e8] disabled:cursor-not-allowed disabled:bg-[#aebbd0]">{mutation.isPending ? "Mapping your topic…" : "ϟ Diagnose my understanding"}</button>
          </div>
        </form>
      </section>
    </AppShell>
  );
}
