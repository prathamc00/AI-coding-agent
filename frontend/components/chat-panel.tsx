"use client";

import { ChatMessage } from "@/lib/api";
import { Loader2, Sparkles, Wrench } from "lucide-react";
import { FormEvent, useState } from "react";

type Props = {
  messages: ChatMessage[];
  onSendChat: (message: string) => Promise<void>;
  onGenerateCode: (prompt: string, errorFixMode?: boolean) => Promise<void>;
  busy: boolean;
  reviewNotes: string;
};

export default function ChatPanel({ messages, onSendChat, onGenerateCode, busy, reviewNotes }: Props) {
  const [chatInput, setChatInput] = useState("");
  const [genInput, setGenInput] = useState("");

  const submitChat = async (e: FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    await onSendChat(chatInput);
    setChatInput("");
  };

  const submitGenerate = async (e: FormEvent) => {
    e.preventDefault();
    if (!genInput.trim()) return;
    await onGenerateCode(genInput, false);
    setGenInput("");
  };

  return (
    <div className="flex h-full flex-col gap-3">
      <section className="flex-1 overflow-hidden rounded-xl border border-border bg-slate-900/80">
        <div className="border-b border-border px-3 py-2 text-xs uppercase tracking-wide text-slate-400">Chat</div>
        <div className="h-[44vh] space-y-3 overflow-auto p-3">
          {messages.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border p-3 text-xs text-slate-400">
              Ask questions about the codebase, architecture, or bug locations.
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={`${msg.role}-${idx}-${msg.created_at ?? ""}`}
                className={`rounded-lg px-3 py-2 text-xs ${msg.role === "user" ? "ml-7 bg-cyan-500/20 text-cyan-50" : "mr-7 bg-slate-800 text-slate-200"}`}
              >
                {msg.content}
              </div>
            ))
          )}
        </div>
        <form onSubmit={submitChat} className="border-t border-border p-2">
          <div className="flex gap-2">
            <input
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Explain auth flow..."
              className="w-full rounded-lg border border-border bg-slate-950 px-3 py-2 text-xs text-slate-100"
            />
            <button
              type="submit"
              disabled={busy}
              className="rounded-lg bg-cyan-500 px-3 py-2 text-xs font-semibold text-slate-900 disabled:opacity-50"
            >
              {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Send"}
            </button>
          </div>
        </form>
      </section>

      <section className="rounded-xl border border-border bg-slate-900/80 p-3">
        <p className="mb-2 flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
          <Sparkles className="h-3.5 w-3.5" />
          Generate Code
        </p>
        <form onSubmit={submitGenerate} className="space-y-2">
          <textarea
            value={genInput}
            onChange={(e) => setGenInput(e.target.value)}
            placeholder="Add forgot password flow"
            className="h-20 w-full rounded-lg border border-border bg-slate-950 px-3 py-2 text-xs text-slate-100"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={busy}
              className="rounded-lg bg-cyan-500 px-3 py-2 text-xs font-semibold text-slate-900 disabled:opacity-50"
            >
              {busy ? "Generating..." : "Generate Changes"}
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => onGenerateCode("Fix all build errors", true)}
              className="inline-flex items-center gap-1 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs font-semibold text-amber-100 disabled:opacity-50"
            >
              <Wrench className="h-3.5 w-3.5" />
              Fix All Build Errors
            </button>
          </div>
        </form>
        {reviewNotes ? <p className="mt-2 text-xs text-slate-300">Review: {reviewNotes}</p> : null}
      </section>
    </div>
  );
}
