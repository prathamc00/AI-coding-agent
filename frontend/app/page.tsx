"use client";

import ChatPanel from "@/components/chat-panel";
import CommandBar from "@/components/command-bar";
import DiffViewer from "@/components/diff-viewer";
import EditorPanel from "@/components/editor-panel";
import FileTree from "@/components/file-tree";
import RepoLoader from "@/components/repo-loader";
import {
  ChatMessage,
  FileNode,
  ProposedChange,
  applyDiff,
  generateCode,
  getFiles,
  getHistory,
  sendChat,
} from "@/lib/api";
import { useMutation } from "@tanstack/react-query";
import { Code2, History, Layers3, RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

export default function HomePage() {
  const [repoId, setRepoId] = useState<string | null>(null);
  const [tree, setTree] = useState<FileNode[]>([]);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [changes, setChanges] = useState<ProposedChange[]>([]);
  const [acceptedMap, setAcceptedMap] = useState<Record<string, boolean>>({});
  const [reviewNotes, setReviewNotes] = useState("");
  const [lastCommandLogs, setLastCommandLogs] = useState("");
  const [lastCommandLabel, setLastCommandLabel] = useState("");

  useEffect(() => {
    const persisted = localStorage.getItem("repo_id");
    if (persisted) {
      setRepoId(persisted);
    }
  }, []);

  const refreshRepo = async (id: string) => {
    const [filesResponse, historyResponse] = await Promise.all([getFiles(id), getHistory(id)]);
    setTree(filesResponse.tree || []);
    setMessages(historyResponse.messages || []);
  };

  useEffect(() => {
    if (!repoId) return;
    refreshRepo(repoId).catch(() => undefined);
  }, [repoId]);

  const selectFile = async (path: string) => {
    if (!repoId) return;
    setSelectedPath(path);
    const filesResponse = await getFiles(repoId, path);
    setFileContent(filesResponse.content || "");
  };

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      if (!repoId) throw new Error("Load a repository first");
      return sendChat(repoId, message);
    },
    onMutate: async (message) => {
      setMessages((prev) => [...prev, { role: "user", content: message }]);
    },
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
    },
  });

  const generateMutation = useMutation({
    mutationFn: async ({ prompt, errorFixMode }: { prompt: string; errorFixMode?: boolean }) => {
      if (!repoId) throw new Error("Load a repository first");
      return generateCode({
        repoId,
        prompt,
        focusPaths: selectedPath ? [selectedPath] : [],
        terminalLogs: lastCommandLogs || undefined,
        errorFixMode,
      });
    },
    onSuccess: (data) => {
      setChanges(data.proposed_changes || []);
      setReviewNotes(data.review_notes || "");
      const defaults: Record<string, boolean> = {};
      (data.proposed_changes || []).forEach((c) => {
        defaults[c.path] = true;
      });
      setAcceptedMap(defaults);
    },
  });

  const applyMutation = useMutation({
    mutationFn: async () => {
      if (!repoId) throw new Error("Load a repository first");
      const acceptedChanges = changes
        .filter((change) => acceptedMap[change.path])
        .map((change) => ({ path: change.path, new_content: change.new_content }));
      return applyDiff(repoId, acceptedChanges);
    },
    onSuccess: async () => {
      if (!repoId) return;
      await refreshRepo(repoId);
      if (selectedPath) {
        await selectFile(selectedPath);
      }
      setChanges([]);
      setAcceptedMap({});
    },
  });

  const historyPreview = useMemo(() => messages.slice(-8), [messages]);

  return (
    <main className="h-screen p-4">
      <div className="grid h-full grid-cols-[290px_minmax(450px,1fr)_420px] gap-4">
        <aside className="flex h-full flex-col gap-3">
          <RepoLoader onLoaded={setRepoId} />

          <section className="flex-1 overflow-hidden rounded-xl border border-border bg-slate-900/70 p-3">
            <div className="mb-2 flex items-center justify-between">
              <p className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
                <Layers3 className="h-3.5 w-3.5" />
                Files
              </p>
              {repoId ? (
                <button
                  type="button"
                  onClick={() => refreshRepo(repoId)}
                  className="rounded-md border border-border p-1 text-slate-400 hover:text-cyan-200"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                </button>
              ) : null}
            </div>
            <div className="h-[40vh] overflow-auto">
              <FileTree tree={tree} selectedPath={selectedPath} onSelectFile={selectFile} />
            </div>
          </section>

          <section className="overflow-hidden rounded-xl border border-border bg-slate-900/70 p-3">
            <p className="mb-2 flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
              <History className="h-3.5 w-3.5" />
              History
            </p>
            <div className="max-h-40 space-y-2 overflow-auto">
              {historyPreview.length === 0 ? (
                <p className="text-xs text-slate-500">No chat history yet.</p>
              ) : (
                historyPreview.map((msg, idx) => (
                  <div key={`${msg.role}-${idx}`} className="rounded-md bg-slate-800/60 px-2 py-1 text-[11px] text-slate-300">
                    <span className="font-semibold text-slate-200">{msg.role}:</span> {msg.content.slice(0, 120)}
                  </div>
                ))
              )}
            </div>
          </section>
        </aside>

        <section className="flex h-full flex-col gap-3">
          <CommandBar
            repoId={repoId || ""}
            onCommandResult={(logs, status, command) => {
              setLastCommandLogs(logs);
              setLastCommandLabel(`${command} (${status})`);
            }}
          />

          <div className="grid flex-1 grid-rows-[1fr_auto] gap-3 overflow-hidden">
            <EditorPanel filePath={selectedPath} value={fileContent} readOnly />

            <section className="rounded-xl border border-border bg-slate-900/70 p-3">
              <div className="mb-2 flex items-center justify-between">
                <p className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
                  <Code2 className="h-3.5 w-3.5" />
                  Proposed Changes
                </p>
                <button
                  type="button"
                  disabled={applyMutation.isPending || changes.length === 0}
                  onClick={() => applyMutation.mutate()}
                  className="rounded-md bg-emerald-500/20 px-2 py-1 text-xs text-emerald-100 disabled:opacity-40"
                >
                  {applyMutation.isPending ? "Applying..." : "Apply Accepted"}
                </button>
              </div>
              <DiffViewer
                changes={changes}
                accepted={acceptedMap}
                onToggle={(path, value) => setAcceptedMap((prev) => ({ ...prev, [path]: value }))}
                onAcceptAll={() => {
                  const next: Record<string, boolean> = {};
                  changes.forEach((change) => {
                    next[change.path] = true;
                  });
                  setAcceptedMap(next);
                }}
              />
            </section>
          </div>

          <section className="max-h-44 overflow-auto rounded-xl border border-border bg-slate-900/70 p-3">
            <p className="mb-1 text-xs uppercase tracking-wide text-slate-400">Terminal Output {lastCommandLabel ? `- ${lastCommandLabel}` : ""}</p>
            <pre className="text-[11px] text-slate-300">{lastCommandLogs || "No command output yet."}</pre>
          </section>
        </section>

        <aside className="h-full">
          <ChatPanel
            messages={messages}
            busy={chatMutation.isPending || generateMutation.isPending}
            onSendChat={async (message) => {
              await chatMutation.mutateAsync(message);
            }}
            onGenerateCode={async (prompt, errorFixMode) => {
              await generateMutation.mutateAsync({ prompt, errorFixMode });
            }}
            reviewNotes={reviewNotes}
          />
        </aside>
      </div>
    </main>
  );
}
