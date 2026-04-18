"use client";

import { FileNode } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronRight, FileCode2, Folder } from "lucide-react";
import { useMemo, useState } from "react";

type Props = {
  tree: FileNode[];
  selectedPath: string | null;
  onSelectFile: (path: string) => void;
};

function NodeItem({
  node,
  level,
  selectedPath,
  onSelectFile,
}: {
  node: FileNode;
  level: number;
  selectedPath: string | null;
  onSelectFile: (path: string) => void;
}) {
  const [open, setOpen] = useState(level < 1);

  if (node.type === "file") {
    return (
      <button
        type="button"
        onClick={() => onSelectFile(node.path)}
        className={cn(
          "flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-xs text-slate-300 transition hover:bg-slate-800/80",
          selectedPath === node.path && "bg-cyan-500/20 text-cyan-100",
        )}
        style={{ paddingLeft: `${level * 14 + 8}px` }}
      >
        <FileCode2 className="h-3.5 w-3.5 shrink-0" />
        <span className="truncate">{node.name}</span>
      </button>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-xs text-slate-200 transition hover:bg-slate-800/80"
        style={{ paddingLeft: `${level * 14 + 8}px` }}
      >
        {open ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <Folder className="h-3.5 w-3.5 text-cyan-300" />
        <span className="truncate">{node.name}</span>
      </button>
      {open && (
        <div>
          {node.children.map((child) => (
            <NodeItem
              key={child.path}
              node={child}
              level={level + 1}
              selectedPath={selectedPath}
              onSelectFile={onSelectFile}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function FileTree({ tree, selectedPath, onSelectFile }: Props) {
  const empty = useMemo(() => tree.length === 0, [tree.length]);

  if (empty) {
    return <div className="rounded-lg border border-dashed border-slate-700 p-3 text-xs text-slate-400">No files yet.</div>;
  }

  return (
    <div className="space-y-1">
      {tree.map((node) => (
        <NodeItem key={node.path} node={node} level={0} selectedPath={selectedPath} onSelectFile={onSelectFile} />
      ))}
    </div>
  );
}
