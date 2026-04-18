import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 120000,
});

export type FileNode = {
  name: string;
  path: string;
  type: "file" | "directory";
  children: FileNode[];
};

export type ProposedChange = {
  path: string;
  old_content: string;
  new_content: string;
  diff: string;
  rationale: string;
};

export type ChatMessage = {
  id?: number;
  repo_id?: string;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
};

export type HealthResponse = {
  status: string;
  provider?: string;
  model?: string;
};

export async function getHealth() {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

export async function uploadRepo(params: { files?: File[]; localPath?: string }) {
  const formData = new FormData();
  params.files?.forEach((file) => {
    const relativePath = (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name;
    formData.append("files", file, relativePath);
  });
  if (params.localPath) {
    formData.append("local_path", params.localPath);
  }

  const { data } = await api.post<{ repo_id: string; message: string }>("/api/upload-repo", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getFiles(repoId: string, path?: string) {
  const { data } = await api.get<{ tree: FileNode[]; content: string | null }>("/api/files", {
    params: { repo_id: repoId, path },
  });
  return data;
}

export async function sendChat(repoId: string, message: string) {
  const { data } = await api.post<{ answer: string }>("/api/chat", { repo_id: repoId, message });
  return data;
}

export async function generateCode(payload: {
  repoId: string;
  prompt: string;
  focusPaths?: string[];
  terminalLogs?: string;
  errorFixMode?: boolean;
}) {
  const { data } = await api.post<{
    plan: string[];
    proposed_changes: ProposedChange[];
    review_notes: string;
  }>("/api/generate-code", {
    repo_id: payload.repoId,
    prompt: payload.prompt,
    focus_paths: payload.focusPaths || [],
    terminal_logs: payload.terminalLogs || null,
    error_fix_mode: payload.errorFixMode || false,
  });
  return data;
}

export async function applyDiff(repoId: string, changes: Array<{ path: string; new_content: string }>) {
  const { data } = await api.post<{ updated_files: string[] }>("/api/apply-diff", {
    repo_id: repoId,
    changes,
  });
  return data;
}

export async function runCommand(repoId: string, command: string) {
  const { data } = await api.post<{ command: string; status: string; output: string }>("/api/run-command", {
    repo_id: repoId,
    command,
  });
  return data;
}

export async function getHistory(repoId: string) {
  const { data } = await api.get<{ messages: ChatMessage[] }>("/api/history", { params: { repo_id: repoId } });
  return data;
}

export async function getLastCommand(repoId: string) {
  const { data } = await api.get<{ command: string; status: string; output: string }>("/api/last-command", {
    params: { repo_id: repoId },
  });
  return data;
}
