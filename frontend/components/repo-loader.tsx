"use client";

import { uploadRepo } from "@/lib/api";
import { useMutation } from "@tanstack/react-query";
import { FolderUp, Loader2 } from "lucide-react";
import { useState } from "react";

type Props = {
  onLoaded: (repoId: string) => void;
};

export default function RepoLoader({ onLoaded }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [localPath, setLocalPath] = useState("");
  const mutation = useMutation({
    mutationFn: () => uploadRepo({ files, localPath: localPath || undefined }),
    onSuccess: (data) => {
      localStorage.setItem("repo_id", data.repo_id);
      onLoaded(data.repo_id);
    },
  });

  return (
    <div className="space-y-3 rounded-xl border border-border bg-slate-900/80 p-4">
      <div className="flex items-center gap-2 text-sm text-slate-100">
        <FolderUp className="h-4 w-4 text-cyan-300" />
        <span>Load project folder</span>
      </div>

      <input
        className="w-full rounded-lg border border-border bg-slate-950 px-3 py-2 text-xs text-slate-200"
        placeholder="Optional local path (backend machine)"
        value={localPath}
        onChange={(e) => setLocalPath(e.target.value)}
      />

      <input
        type="file"
        multiple
        onChange={(e) => setFiles(Array.from(e.target.files || []))}
        className="w-full text-xs text-slate-300"
        {...({ webkitdirectory: "true", directory: "true" } as any)}
      />

      <button
        type="button"
        onClick={() => mutation.mutate()}
        disabled={mutation.isPending || (!localPath && files.length === 0)}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-500 px-3 py-2 text-xs font-semibold text-slate-900 disabled:opacity-50"
      >
        {mutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
        Index Repository
      </button>

      {mutation.error ? (
        <p className="text-xs text-rose-300">{(mutation.error as Error).message}</p>
      ) : null}
    </div>
  );
}
