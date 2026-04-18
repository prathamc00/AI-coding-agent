"use client";

import { runCommand } from "@/lib/api";
import { useMutation } from "@tanstack/react-query";
import { Loader2, PlayCircle } from "lucide-react";

const COMMANDS = ["npm install", "npm run dev", "npm run build", "pytest", "lint"];

type Props = {
  repoId: string;
  onCommandResult: (logs: string, status: string, command: string) => void;
};

export default function CommandBar({ repoId, onCommandResult }: Props) {
  const mutation = useMutation({
    mutationFn: (command: string) => {
      if (!repoId) throw new Error("Load a repository first");
      return runCommand(repoId, command);
    },
    onSuccess: (data) => onCommandResult(data.output, data.status, data.command),
  });

  return (
    <div className="space-y-2 rounded-xl border border-border bg-slate-900/70 p-3">
      <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
        <PlayCircle className="h-3.5 w-3.5" />
        Commands
      </div>
      <div className="grid grid-cols-2 gap-2">
        {COMMANDS.map((command) => (
          <button
            type="button"
            key={command}
            onClick={() => mutation.mutate(command)}
            disabled={mutation.isPending || !repoId}
            className="rounded-lg border border-border bg-slate-800/70 px-2 py-2 text-xs text-slate-200 transition hover:border-cyan-500/40 disabled:opacity-40"
          >
            {mutation.isPending && mutation.variables === command ? (
              <span className="inline-flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" />
                Running
              </span>
            ) : (
              command
            )}
          </button>
        ))}
      </div>
      {mutation.error ? <p className="text-xs text-rose-300">{(mutation.error as Error).message}</p> : null}
      {mutation.data ? (
        <p className="text-xs text-slate-400">
          Last run: <span className={mutation.data.status === "success" ? "text-emerald-300" : "text-rose-300"}>{mutation.data.command}</span>
        </p>
      ) : null}
    </div>
  );
}
