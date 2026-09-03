"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
export type WorkspaceSection =
  | "overview"
  | "knowledge-map"
  | "diagnosis"
  | "root-gap"
  | "ai-tutor"
  | "teach-back"
  | "progress"
  | "history";

interface AppShellProps {
  children: React.ReactNode;
  status?: string;
  topic?: string | null;
  activeSection?: WorkspaceSection;
  onNewSession?: () => void;
  onSectionChange?: (section: WorkspaceSection) => void;
}

const navigation: Array<{ id: WorkspaceSection; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "knowledge-map", label: "Knowledge Map" },
  { id: "diagnosis", label: "Diagnosis" },
  { id: "teach-back", label: "Teach-Back" },
  { id: "progress", label: "Progress" },
];

function sectionForStatus(status?: string): WorkspaceSection {
  if (status === "diagnosing") return "diagnosis";
  if (status === "tutoring") return "knowledge-map";
  if (status === "teachback") return "teach-back";
  if (status === "completed") return "progress";
  return "overview";
}

function statusLabel(status?: string) {
  if (!status) return "New Session";
  if (status === "analyzing") return "Analyzing";
  if (status === "diagnosing") return "Diagnosis";
  if (status === "tutoring") return "Learning";
  if (status === "teachback") return "Teach-Back";
  if (status === "completed") return "Complete";
  if (status === "abandoned") return "Setup issue";
  return "Session";
}

export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3" aria-label="RootLearn">
      <span className="brand-mark" aria-hidden="true">
        <i />
        <b />
        <em />
      </span>
      {!compact && <span className="text-[22px] font-bold tracking-tight text-[#111827]">RootLearn</span>}
    </div>
  );
}

function NavIcon({ section }: { section: WorkspaceSection }) {
  const common = "h-[22px] w-[22px]";

  if (section === "overview") return <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>;
  if (section === "knowledge-map") return <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="9" y="2.5" width="6" height="5" rx="1"/><rect x="2.5" y="16.5" width="6" height="5" rx="1"/><rect x="15.5" y="16.5" width="6" height="5" rx="1"/><path d="M12 7.5v4.5M5.5 16.5V12H18.5v4.5"/></svg>;
  if (section === "diagnosis") return <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M9 3v4l-3.5 3.5a6 6 0 0 0 12 0L14 7V3"/><path d="M7 3h4M12 14h6M18 11v6"/></svg>;
  if (section === "root-gap") return <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5h.01"/></svg>;
  if (section === "ai-tutor") return <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="m12 2 1.4 4.1L17.5 7.5l-4.1 1.4L12 13l-1.4-4.1-4.1-1.4 4.1-1.4L12 2Z"/><path d="m18.5 13 .8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8.8-2.2ZM5 13.5l.8 2.2 2.2.8-2.2.8L5 19.5l-.8-2.2-2.2-.8 2.2-.8L5 13.5Z"/></svg>;
  if (section === "teach-back") return <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v17H6.5A2.5 2.5 0 0 0 4 22V5.5ZM20 5.5A2.5 2.5 0 0 0 17.5 3H13v17h4.5A2.5 2.5 0 0 1 20 22V5.5Z"/></svg>;
  if (section === "progress") return <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="m3 17 5-5 4 3 8-9"/><path d="M15 6h5v5"/></svg>;
  return <svg className={common} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M4 4v5h5"/><path d="M5.5 16.5A8 8 0 1 0 5 8.5L4 9"/><path d="M12 7v5l3 2"/></svg>;
}

export default function AppShell({ children, status, topic, activeSection, onNewSession, onSectionChange }: AppShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const selected = activeSection ?? sectionForStatus(status);
  const startNew = onNewSession ?? (() => router.push("/"));
  const [darkMode, setDarkMode] = useState(false);

  const navigateToSection = (section: WorkspaceSection) => {
    if (onSectionChange) {
      onSectionChange(section);
      return;
    }

    if (section === "overview") {
      router.push("/");
      return;
    }

    // AppShell is also used by a few nested session pages. Route those
    // sidebar clicks back through the main session workspace while preserving
    // ownership/query parameters.
    const sessionMatch = pathname.match(/^\/session\/([^/]+)/);
    if (sessionMatch) {
      const nextParams = new URLSearchParams(searchParams.toString());
      nextParams.set("section", section);
      router.push(`/session/${sessionMatch[1]}?${nextParams.toString()}`);
      return;
    }

  };

  return (
    <div className={`min-h-screen text-[#111827] ${darkMode ? "bg-[#e9edf4]" : "bg-[#f8f9fb]"}`}>
      <header className="fixed inset-x-0 top-0 z-40 flex h-[88px] items-center border-b border-[#e3e5e8] bg-white/95 backdrop-blur">
        <div className="hidden h-full w-[292px] shrink-0 items-center border-r border-[#e3e5e8] bg-white px-8 lg:flex">
          <BrandMark />
        </div>
        <div className="flex flex-1 items-center justify-between gap-5 px-5 lg:px-10">
          <div className="flex min-w-0 items-center gap-5">
            <div className="lg:hidden"><BrandMark compact /></div>
            <span className="rounded-full bg-[#e8f1ff] px-4 py-2 text-sm font-semibold text-[#2878e9]">{statusLabel(status)}</span>
            {topic && (
              <div className="hidden min-w-0 sm:block">
                <p className="truncate text-lg font-semibold text-[#111827]">{topic}</p>
                <p className="mt-0.5 text-sm text-[#7d818b]">Guided learning session</p>
              </div>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden items-center rounded-full border border-[#dfe2e7] bg-white p-1 shadow-sm md:flex" aria-label="Appearance">
              <button type="button" onClick={() => setDarkMode(false)} aria-label="Use light appearance" aria-pressed={!darkMode} className={`flex h-8 w-9 items-center justify-center rounded-full text-lg ${!darkMode ? "bg-[#f1f2f4] text-[#111827]" : "text-[#7c818a]"}`}>☼</button>
              <button type="button" onClick={() => setDarkMode(true)} aria-label="Use dim appearance" aria-pressed={darkMode} className={`flex h-8 w-9 items-center justify-center rounded-full text-lg ${darkMode ? "bg-[#e8f1ff] text-[#2878e9]" : "text-[#111827]"}`}>◔</button>
            </div>
            <button type="button" aria-label="Help" className="hidden h-10 w-10 items-center justify-center rounded-full border-2 border-[#aeb4bd] text-lg font-bold text-[#69707a] sm:flex">?</button>
            <button type="button" onClick={startNew} className="rounded-full bg-[#4b98f9] px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#287fe9] sm:px-7">
              <span className="mr-2 text-xl font-light leading-none">＋</span> New session
            </button>
            <span className="hidden h-12 w-12 items-center justify-center rounded-full bg-[#f1f2f4] text-sm font-semibold text-[#22252a] sm:flex">RL</span>
          </div>
        </div>
      </header>

      <aside className="fixed bottom-0 left-0 top-[88px] z-30 hidden w-[292px] flex-col border-r border-[#e3e5e8] bg-white text-[#171a20] lg:flex">
        <div className="px-8 pb-4 pt-8 text-xs font-bold uppercase tracking-[0.14em] text-[#747983]">Workspace</div>
        <nav className="space-y-1.5 px-5" aria-label="Session workspace">
          {navigation.map((item) => {
            const isActive = item.id === selected;
            return (
              <button 
                key={item.id} 
                type="button"
                onClick={() => navigateToSection(item.id)}
                className={`flex h-12 w-full items-center gap-4 rounded-xl px-4 text-[16px] font-medium transition-colors ${isActive ? "bg-[#e8f1ff] text-[#2878e9]" : "text-[#181b21] hover:bg-[#f4f5f7]"}`}
                aria-label={`${item.label}${isActive ? ' (current)' : ''}`}
                aria-current={isActive ? 'page' : undefined}
              >
                <span className="flex h-6 w-6 items-center justify-center" aria-hidden="true"><NavIcon section={item.id} /></span>
                {item.label}
              </button>
            );
          })}
        </nav>
        <div className="mt-auto p-5">
          <div className="rounded-2xl bg-[#f4f4f5] p-5 text-[#252930]">
            <p className="mb-2 flex items-center gap-2 font-semibold"><span className="flex h-5 w-5 items-center justify-center rounded-full border-2 border-[#4b98f9] text-xs text-[#2878e9]">↗</span>{status === "analyzing" ? "Diagnosis in progress" : status === "completed" ? "Session complete" : status === "abandoned" ? "Setup needs attention" : "Guided session"}</p>
            <p className="text-sm leading-6 text-[#747983]">{status === "analyzing" ? "Sections unlock once your knowledge map is ready." : status === "completed" ? "Review what you mastered and start again anytime." : status === "abandoned" ? "The knowledge map could not be generated. You can retry safely." : "Follow the path from your root gap to real understanding."}</p>
          </div>
        </div>
      </aside>

      <div className="pt-[88px] lg:pl-[292px]">
        <nav className="flex gap-2 overflow-x-auto border-b border-[#dfe6ef] bg-white px-4 py-3 lg:hidden" aria-label="Mobile session workspace">
          {navigation.slice(0, 6).map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => navigateToSection(item.id)}
              aria-current={item.id === selected ? "page" : undefined}
              className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-semibold ${item.id === selected ? "bg-[#e7efff] text-[#1463ff]" : "text-[#748097] hover:bg-[#f0f4fa] hover:text-[#10213d]"}`}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <main className="min-h-[calc(100vh-88px)]">{children}</main>
      </div>
    </div>
  );
}
