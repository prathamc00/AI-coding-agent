"use client";

import dynamic from "next/dynamic";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

type Props = {
  filePath: string | null;
  value: string;
  onChange?: (next: string) => void;
  readOnly?: boolean;
};

function languageFromPath(path: string | null) {
  if (!path) return "plaintext";
  if (path.endsWith(".ts") || path.endsWith(".tsx")) return "typescript";
  if (path.endsWith(".js") || path.endsWith(".jsx")) return "javascript";
  if (path.endsWith(".py")) return "python";
  if (path.endsWith(".json")) return "json";
  if (path.endsWith(".md")) return "markdown";
  if (path.endsWith(".css") || path.endsWith(".scss")) return "css";
  if (path.endsWith(".html")) return "html";
  if (path.endsWith(".yml") || path.endsWith(".yaml")) return "yaml";
  return "plaintext";
}

export default function EditorPanel({ filePath, value, onChange, readOnly = true }: Props) {
  return (
    <div className="h-full overflow-hidden rounded-xl border border-border bg-slate-950/90 shadow-glow">
      <div className="border-b border-border bg-slate-900/70 px-3 py-2 text-xs text-slate-300">
        {filePath || "No file selected"}
      </div>
      <div className="h-[calc(100%-37px)]">
        <MonacoEditor
          theme="vs-dark"
          language={languageFromPath(filePath)}
          value={value}
          onChange={(next) => onChange?.(next || "")}
          options={{
            readOnly,
            minimap: { enabled: false },
            fontSize: 13,
            wordWrap: "on",
            smoothScrolling: true,
          }}
        />
      </div>
    </div>
  );
}
