"use client";

import { ProposedChange } from "@/lib/api";
import { Check, X } from "lucide-react";

type Props = {
  changes: ProposedChange[];
  accepted: Record<string, boolean>;
  onToggle: (path: string, value: boolean) => void;
  onAcceptAll: () => void;
};

export default function DiffViewer({ changes, accepted, onToggle, onAcceptAll }: Props) {
  if (changes.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border p-3 text-xs text-slate-400">
        No proposed changes yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wide text-slate-400">Diff Viewer</p>
        <button
          type="button"
          onClick={onAcceptAll}
          className="rounded-md bg-cyan-500/20 px-2 py-1 text-xs text-cyan-100"
        >
          Accept All
        </button>
      </div>

      {changes.map((change) => (
        <div key={change.path} className="rounded-xl border border-border bg-slate-900/70 p-2">
          <div className="mb-2 flex items-center justify-between gap-2">
            <div>
              <p className="text-xs font-semibold text-slate-100">{change.path}</p>
              <p className="text-[11px] text-slate-400">{change.rationale}</p>
            </div>
            <div className="flex gap-1">
              <button
                type="button"
                onClick={() => onToggle(change.path, true)}
                className={`rounded-md px-2 py-1 text-xs ${accepted[change.path] ? "bg-emerald-500/20 text-emerald-200" : "bg-slate-800 text-slate-300"}`}
              >
                <span className="inline-flex items-center gap-1">
                  <Check className="h-3 w-3" />
                  Accept
                </span>
              </button>
              <button
                type="button"
                onClick={() => onToggle(change.path, false)}
                className={`rounded-md px-2 py-1 text-xs ${accepted[change.path] === false ? "bg-rose-500/20 text-rose-200" : "bg-slate-800 text-slate-300"}`}
              >
                <span className="inline-flex items-center gap-1">
                  <X className="h-3 w-3" />
                  Reject
                </span>
              </button>
            </div>
          </div>
          <pre className="max-h-52 overflow-auto rounded-lg bg-slate-950 p-2 text-[11px] leading-relaxed text-slate-200">{change.diff}</pre>
        </div>
      ))}
    </div>
  );
}
