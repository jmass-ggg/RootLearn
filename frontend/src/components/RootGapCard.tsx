"use client";

import { RootGapResult } from "@/types/root-gap";

interface RootGapCardProps {
  rootGap: RootGapResult | null;
  isLoading: boolean;
  onFixGap: () => void;
}

export default function RootGapCard({ rootGap, isLoading, onFixGap }: RootGapCardProps) {
  if (isLoading) {
    return <div className="soft-card flex min-h-[360px] items-center justify-center"><span className="h-12 w-12 animate-spin rounded-full border-4 border-[#c9d9ff] border-t-[#1463ff]" /><span className="sr-only">Loading root gap</span></div>;
  }
  if (!rootGap) {
    return <div className="soft-card flex min-h-[280px] items-center justify-center p-8 text-center text-[#718096]">No root gap identified yet</div>;
  }

  const gap = rootGap.root_gap;
  return (
    <article className="soft-card overflow-hidden p-7 sm:p-10">
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.1em] text-[#718096]">Root Gap Identified</p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <h2 className="text-3xl font-bold">{gap.concept_name}</h2>
            <span className="rounded-full border-2 border-[#d2e90d] px-3 py-1 text-sm font-semibold text-[#1463ff]">Root concept</span>
          </div>
        </div>
        <span className="flex h-16 w-16 items-center justify-center rounded-2xl border-2 border-[#bcd0ff] bg-[#f1f6ff] text-3xl text-[#1463ff]">▱</span>
      </div>

      <p className="mt-2 text-sm text-[#718096]">This is blocking your understanding</p>
      <p className="mt-7 max-w-4xl text-lg leading-8 text-[#30415d]">{rootGap.message}</p>

      <div className="mt-7 rounded-2xl border border-[#dce5ef] bg-[#f6f8fb] p-6">
        <h3 className="font-bold"><span className="mr-2 text-[#20a572]">✣</span>Why this gap matters:</h3>
        <ul className="mt-3 space-y-2 text-[#68758c]">{gap.reasons.map((reason) => <li key={reason} className="flex gap-2 leading-7"><span aria-hidden="true">•</span><span>{reason}</span></li>)}</ul>
      </div>

      <div className="mt-7 grid grid-cols-3 gap-3">
        <Metric label="Mastery" value={`${Math.round(gap.mastery * 100)}%`} color="text-[#dc4b50]" />
        <Metric label="Confidence" value={`${Math.round(gap.confidence * 100)}%`} color="text-[#1463ff]" />
        <Metric label="Gap Score" value={gap.gap_score.toFixed(2)} color="text-[#d39122]" />
      </div>

      <div className="mt-8 flex flex-col items-center justify-between gap-4 border-t border-[#e1e7ef] pt-7 sm:flex-row">
        <p className="text-sm text-[#718096]">Let&apos;s work through this concept together using Socratic guidance.</p>
        <button type="button" aria-label="Fix This Gap" onClick={onFixGap} className="w-full rounded-xl bg-[#1463ff] px-6 py-3.5 font-semibold text-white transition hover:bg-[#0754e8] sm:w-auto">Start guided learning →</button>
      </div>
    </article>
  );
}

function Metric({ label, value, color }: { label: string; value: string; color: string }) {
  return <div className="rounded-xl border border-[#dfe6ef] bg-white p-4"><p className="text-xs font-semibold uppercase tracking-wide text-[#8591a4]">{label}</p><p className={`mt-1 text-xl font-bold ${color}`}>{value}</p></div>;
}
