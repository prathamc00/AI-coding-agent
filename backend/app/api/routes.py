from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.agents.workflow import workflow
from app.core.database import get_db
from app.models.entities import ChatMessage, CommandRun
from app.schemas.api import (
    ApplyDiffRequest,
    ApplyDiffResponse,
    ChatRequest,
    ChatResponse,
    FilesResponse,
    GenerateCodeRequest,
    GenerateCodeResponse,
    HistoryItem,
    HistoryResponse,
    RunCommandRequest,
    RunCommandResponse,
    UploadRepoResponse,
)
from app.services.command_service import run_project_command
from app.services.llm_service import llm_service
from app.services.repo_service import (
    build_file_tree,
    create_repo_from_upload,
    read_file,
    resolve_repo,
    search_code,
    write_file,
)

router = APIRouter(prefix="/api", tags=["agent"])


@router.post("/upload-repo", response_model=UploadRepoResponse)
async def upload_repo(
    files: list[UploadFile] = File(default=[]),
    local_path: str | None = Form(default=None),
):
    repo_id = create_repo_from_upload(files=files, local_path=local_path)
    return UploadRepoResponse(repo_id=repo_id, message="Repository indexed successfully")


@router.get("/files", response_model=FilesResponse)
def get_files(repo_id: str, path: str | None = None):
    repo = resolve_repo(repo_id)
    tree = build_file_tree(repo)
    content = read_file(repo, path) if path else None
    return FilesResponse(tree=tree, content=content)


@router.post("/chat", response_model=ChatResponse)
def chat_with_repo(payload: ChatRequest, db: Session = Depends(get_db)):
    repo = resolve_repo(payload.repo_id)
    context = search_code(repo, payload.message, limit=8)

    if llm_service.available:
        context_text = "\n\n".join([f"File: {r.path}\nSnippet:\n{r.snippet}" for r in context])
        answer = llm_service.complete_text(
            system_prompt=(
                "You are a precise senior software engineer answering questions about a repository. "
                "If uncertain, say what to inspect next."
            ),
            user_prompt=f"Question: {payload.message}\n\nContext:\n{context_text}",
        )
    else:
        if not context:
            answer = "No relevant files were found for that question. Add OPENAI_API_KEY for richer analysis."
        else:
            bullets = "\n".join([f"- {c.path}" for c in context])
            answer = (
                "OPENAI_API_KEY is not configured, so here are the most relevant files to inspect:\n"
                f"{bullets}"
            )

    db.add(ChatMessage(repo_id=payload.repo_id, role="user", content=payload.message))
    db.add(ChatMessage(repo_id=payload.repo_id, role="assistant", content=answer))
    db.commit()
    return ChatResponse(answer=answer)


@router.post("/generate-code", response_model=GenerateCodeResponse)
def generate_code(payload: GenerateCodeRequest):
    repo = resolve_repo(payload.repo_id)
    plan, proposed_changes, review_notes, _ = workflow.run(
        repo_path=repo,
        task=payload.prompt,
        focus_paths=payload.focus_paths,
        terminal_logs=payload.terminal_logs,
        error_fix_mode=payload.error_fix_mode,
    )
    return GenerateCodeResponse(plan=plan, proposed_changes=proposed_changes, review_notes=review_notes)


@router.post("/apply-diff", response_model=ApplyDiffResponse)
def apply_diff(payload: ApplyDiffRequest):
    repo = resolve_repo(payload.repo_id)
    updated: list[str] = []
    for change in payload.changes:
        write_file(repo, change.path, change.new_content)
        updated.append(change.path)
    return ApplyDiffResponse(updated_files=updated)


@router.post("/run-command", response_model=RunCommandResponse)
def run_command(payload: RunCommandRequest, db: Session = Depends(get_db)):
    repo = resolve_repo(payload.repo_id)
    status, output = run_project_command(repo, payload.command)

    db.add(
        CommandRun(
            repo_id=payload.repo_id,
            command=payload.command,
            status=status,
            output=output,
        )
    )
    db.commit()

    return RunCommandResponse(command=payload.command, status=status, output=output)


@router.get("/history", response_model=HistoryResponse)
def get_history(repo_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.repo_id == repo_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return HistoryResponse(
        messages=[
            HistoryItem(
                id=row.id,
                repo_id=row.repo_id,
                role=row.role,
                content=row.content,
                created_at=row.created_at,
            )
            for row in rows
        ]
    )


@router.get("/last-command", response_model=RunCommandResponse)
def last_command(repo_id: str, db: Session = Depends(get_db)):
    row = (
        db.query(CommandRun)
        .filter(CommandRun.repo_id == repo_id)
        .order_by(desc(CommandRun.created_at))
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="No command run history")
    return RunCommandResponse(command=row.command, status=row.status, output=row.output)
