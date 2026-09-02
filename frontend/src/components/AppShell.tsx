"use client";

import { useRouter } from "next/navigation";
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
}

const navigation: Array<{ id: WorkspaceSection; label: string; icon: string }> = [
  { id: "overview", label: "Overview", icon: "▦" },
  { id: "knowledge-map", label: "Knowledge Map", icon: "⌘" },
  { id: "diagnosis", label: "Diagnosis", icon: "▣" },
  { id: "root-gap", label: "Root Gap", icon: "!" },
  { id: "ai-tutor", label: "AI Tutor", icon: "○" },
  { id: "teach-back", label: "Teach-Back", icon: "▤" },
  { id: "progress", label: "Progress", icon: "↗" },
  { id: "history", label: "Session History", icon: "◷" },
];

function sectionForStatus(status?: string): WorkspaceSection {
  if (status === "diagnosing") return "diagnosis";
  if (status === "tutoring") return "root-gap";
  if (status === "teachback") return "teach-back";
  if (status === "completed") return "progress";
  return "overview";
}

function statusLabel(status?: string) {
  if (!status) return "New Session";
  if (status === "analyzing") return "Analyzing";
  if (status === "diagnosing") return "Diagnosis";
  if (status === "tutoring") return "Root Gap";
  if (status === "teachback") return "Teach-Back";
  if (status === "completed") return "Complete";
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
      {!compact && <span className="text-xl font-bold tracking-tight">RootLearn</span>}
    </div>
  );
}

export default function AppShell({ children, status, topic, activeSection, onNewSession }: AppShellProps) {
  const router = useRouter();
  const selected = activeSection ?? sectionForStatus(status);
  const darkSidebar = selected === "diagnosis" || selected === "ai-tutor";
  const startNew = onNewSession ?? (() => router.push("/"));

  return (
    <div className="min-h-screen bg-[#f4f7fb] text-[#10213d]">
      <header className="fixed inset-x-0 top-0 z-40 flex h-[76px] items-center border-b border-[#dfe6ef] bg-white/95 backdrop-blur">
        <div className={`hidden h-full w-[248px] shrink-0 items-center border-r px-7 lg:flex ${darkSidebar ? "border-white/10 bg-[#062b45] text-white" : "border-[#dfe6ef] bg-white"}`}>
          <BrandMark />
        </div>
        <div className="flex flex-1 items-center justify-between gap-4 px-5 lg:px-8">
          <div className="flex min-w-0 items-center gap-4">
            <div className="lg:hidden"><BrandMark compact /></div>
            <span className="rounded-full bg-[#eaf1ff] px-3 py-1.5 text-sm font-semibold text-[#1463ff]">{statusLabel(status)}</span>
            {topic && (
              <div className="hidden min-w-0 sm:block">
                <p className="truncate font-semibold">{topic}</p>
                <p className="text-xs text-[#7b879d]">Guided learning session</p>
              </div>
            )}
          </div>
          <div className="flex items-center gap-3">
            <button type="button" aria-label="Help" className="hidden h-10 w-10 items-center justify-center rounded-full border border-[#dce4ef] text-lg font-semibold text-[#6f7c92] sm:flex">?</button>
            <button type="button" onClick={startNew} className="rounded-xl bg-[#1463ff] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#0754e8] sm:px-5">
              <span className="mr-1.5 text-lg leading-none">+</span> New session
            </button>
            <span className="hidden h-10 w-10 items-center justify-center rounded-full bg-[#062b45] text-sm font-bold text-white sm:flex">RL</span>
          </div>
        </div>
      </header>

      <aside className={`fixed bottom-0 left-0 top-[76px] z-30 hidden w-[248px] flex-col border-r lg:flex ${darkSidebar ? "border-white/10 bg-[#062b45] text-[#aebdce]" : "border-[#dfe6ef] bg-white text-[#68758c]"}`}>
        <div className="px-5 pb-3 pt-8 text-xs font-bold uppercase tracking-[0.12em] opacity-75">Workspace</div>
        <nav className="space-y-1 px-4" aria-label="Session workspace">
          {navigation.map((item) => {
            const isActive = item.id === selected;
            return (
              <div key={item.id} className={`flex h-12 items-center gap-3 rounded-xl px-4 text-[15px] font-medium ${isActive ? darkSidebar ? "bg-[#0b4773] text-white" : "bg-[#e7efff] text-[#1463ff]" : "opacity-90"}`}>
                <span className={`flex h-6 w-6 items-center justify-center text-lg ${isActive ? "text-[#2d74ff]" : ""}`} aria-hidden="true">{item.icon}</span>
                {item.label}
              </div>
            );
          })}
        </nav>
        <div className="mt-auto p-4">
          <div className={`rounded-2xl border p-4 ${darkSidebar ? "border-white/10 bg-white/5 text-[#d6e0ea]" : "border-[#dfe6ef] bg-[#f7f9fc] text-[#5f6d84]"}`}>
            <p className="mb-1.5 font-semibold text-current">{status === "analyzing" ? "Diagnosis in progress" : status === "completed" ? "Session complete" : "Guided session"}</p>
            <p className="text-sm leading-5 opacity-80">{status === "analyzing" ? "Sections unlock once your knowledge map is ready." : status === "completed" ? "Review what you mastered and start again anytime." : "Follow the path from your root gap to real understanding."}</p>
          </div>
        </div>
      </aside>

      <div className="pt-[76px] lg:pl-[248px]">
        <nav className="flex gap-2 overflow-x-auto border-b border-[#dfe6ef] bg-white px-4 py-3 lg:hidden" aria-label="Mobile session workspace">
          {navigation.slice(0, 6).map((item) => (
            <span key={item.id} className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-semibold ${item.id === selected ? "bg-[#e7efff] text-[#1463ff]" : "text-[#748097]"}`}>{item.label}</span>
          ))}
        </nav>
        <main>{children}</main>
      </div>
    </div>
  );
}
