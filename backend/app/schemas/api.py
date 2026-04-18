from datetime import datetime

from pydantic import BaseModel, Field


class FileNode(BaseModel):
    name: str
    path: str
    type: str
    children: list["FileNode"] = Field(default_factory=list)


FileNode.model_rebuild()


class UploadRepoResponse(BaseModel):
    repo_id: str
    message: str


class ChatRequest(BaseModel):
    repo_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str


class ProposedChange(BaseModel):
    path: str
    old_content: str
    new_content: str
    diff: str
    rationale: str


class GenerateCodeRequest(BaseModel):
    repo_id: str
    prompt: str
    focus_paths: list[str] = Field(default_factory=list)
    terminal_logs: str | None = None
    error_fix_mode: bool = False


class GenerateCodeResponse(BaseModel):
    plan: list[str]
    proposed_changes: list[ProposedChange]
    review_notes: str


class ApplyDiffItem(BaseModel):
    path: str
    new_content: str


class ApplyDiffRequest(BaseModel):
    repo_id: str
    changes: list[ApplyDiffItem]


class ApplyDiffResponse(BaseModel):
    updated_files: list[str]


class RunCommandRequest(BaseModel):
    repo_id: str
    command: str


class RunCommandResponse(BaseModel):
    command: str
    status: str
    output: str


class HistoryItem(BaseModel):
    id: int
    repo_id: str
    role: str
    content: str
    created_at: datetime


class HistoryResponse(BaseModel):
    messages: list[HistoryItem]


class FilesResponse(BaseModel):
    tree: list[FileNode]
    content: str | None = None


class RepoSearchResult(BaseModel):
    path: str
    snippet: str
