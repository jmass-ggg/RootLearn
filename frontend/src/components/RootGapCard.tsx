"use client";

import { RootGapResult } from "@/types/root-gap";
import { Button } from "@/components/ui/Button";
import { FadeIn } from "@/components/ui/FadeTransition";

interface RootGapCardProps {
  rootGap: RootGapResult | null;
  isLoading: boolean;
  onFixGap: () => void;
}

export default function RootGapCard({ rootGap, isLoading, onFixGap }: RootGapCardProps) {
  if (isLoading) {
    return (
      <FadeIn duration={300}>
        <div className="soft-card flex min-h-[360px] items-center justify-center">
          <span className="h-12 w-12 animate-spin rounded-full border-4 border-[#c9d9ff] border-t-[#1463ff]" />
          <span className="sr-only">Loading root gap</span>
        </div>
      </FadeIn>
    );
  }
  
  if (!rootGap) {
    return (
      <FadeIn duration={300}>
        <div className="soft-card flex min-h-[280px] items-center justify-center p-8 text-center text-[#718096]">
          No root gap identified yet
        </div>
      </FadeIn>
    );
  }

  const gap = rootGap.root_gap;
  
  return (
    <FadeIn duration={300}>
      <article className="soft-card overflow-hidden border-l-4 border-brand-lime p-7 sm:p-10">
      {/* Header section with root concept name */}
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
        <div>
          <p className="text-sm font-bold uppercase tracking-[0.1em] text-[#718096]">
            Root Gap Identified
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <h2 className="text-3xl font-bold text-text-heading">
              {gap.concept_name}
            </h2>
            <span className="rounded-full bg-brand-lime px-3 py-1 text-sm font-semibold text-text-heading">
              Root concept
            </span>
          </div>
        </div>
        <span className="flex h-16 w-16 items-center justify-center rounded-2xl border-2 border-brand-lime bg-[#fafce7] text-3xl">
          ⚡
        </span>
      </div>

      <p className="mt-2 text-sm text-text-body">
        This is blocking your understanding
      </p>
      
      {/* API-provided message */}
      <p className="mt-7 max-w-4xl text-lg leading-8 text-[#30415d]">
        {rootGap.message}
      </p>

      {/* Evidence/reasons section */}
      <div className="mt-7 rounded-2xl border border-[#dce5ef] bg-[#f6f8fb] p-6">
        <h3 className="font-bold">
          <span className="mr-2 text-brand-lime">✦</span>
          Why this gap matters:
        </h3>
        <ul className="mt-3 space-y-2 text-[#68758c]">
          {gap.reasons.map((reason, index) => (
            <li key={index} className="flex gap-2 leading-7">
              <span aria-hidden="true">•</span>
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Metrics: mastery, confidence, gap score */}
      <div className="mt-7 grid grid-cols-3 gap-3">
        <Metric 
          label="Mastery" 
          value={`${Math.round(gap.mastery * 100)}%`} 
          color="text-mastery-weak" 
        />
        <Metric 
          label="Confidence" 
          value={`${Math.round(gap.confidence * 100)}%`} 
          color="text-brand-blue" 
        />
        <Metric 
          label="Gap Score" 
          value={gap.gap_score.toFixed(2)} 
          color="text-mastery-learning" 
        />
      </div>

      {/* Action section */}
      <div className="mt-8 flex flex-col items-center justify-between gap-4 border-t border-[#e1e7ef] pt-7 sm:flex-row">
        <p className="text-sm text-text-body">
          Let&apos;s work through this concept together using Socratic guidance.
        </p>
        <Button 
          variant="lime" 
          size="lg"
          onClick={onFixGap}
          className="w-full sm:w-auto"
        >
          Start guided learning →
        </Button>
      </div>
    </article>
    </FadeIn>
  );
}

function Metric({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="rounded-xl border border-[#dfe6ef] bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-[#8591a4]">
        {label}
      </p>
      <p className={`mt-1 text-xl font-bold ${color}`}>
        {value}
      </p>
    </div>
  );
}
