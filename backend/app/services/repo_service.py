from __future__ import annotations

from pathlib import Path
import os
import shutil
import uuid

from fastapi import HTTPException, UploadFile

from app.core.config import REPOS_DIR
from app.schemas.api import FileNode, RepoSearchResult

IGNORED_DIRS = {".git", "node_modules", ".next", "dist", "build", "__pycache__", ".venv", "venv"}
TEXT_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".yml",
    ".yaml",
    ".html",
    ".css",
    ".scss",
    ".toml",
    ".ini",
    ".sh",
    ".env",
    ".txt",
}


def create_repo_from_upload(files: list[UploadFile], local_path: str | None = None) -> str:
    repo_id = str(uuid.uuid4())
    repo_root = REPOS_DIR / repo_id
    repo_root.mkdir(parents=True, exist_ok=True)

    if local_path:
        source = Path(local_path).expanduser().resolve()
        if not source.exists() or not source.is_dir():
            raise HTTPException(status_code=400, detail="Invalid local_path directory")
        _copy_tree(source, repo_root)
        return repo_id

    if not files:
        raise HTTPException(status_code=400, detail="Provide files or local_path")

    for file in files:
        rel_path = Path(file.filename)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            continue
        destination = repo_root / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as f:
            shutil.copyfileobj(file.file, f)

    return repo_id


def _copy_tree(source: Path, destination: Path) -> None:
    for root, dirs, files in os.walk(source):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        src_root = Path(root)
        rel_root = src_root.relative_to(source)
        dest_root = destination / rel_root
        dest_root.mkdir(parents=True, exist_ok=True)
        for name in files:
            src_file = src_root / name
            rel = src_file.relative_to(source)
            out_file = destination / rel
            out_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, out_file)


def resolve_repo(repo_id: str) -> Path:
    repo_path = (REPOS_DIR / repo_id).resolve()
    base = REPOS_DIR.resolve()
    if not repo_path.exists() or base not in repo_path.parents:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo_path


def build_file_tree(repo_path: Path) -> list[FileNode]:
    def walk(path: Path, relative_base: Path) -> list[FileNode]:
        nodes: list[FileNode] = []
        for item in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if item.name in IGNORED_DIRS:
                continue
            rel = item.relative_to(relative_base).as_posix()
            if item.is_dir():
                nodes.append(FileNode(name=item.name, path=rel, type="directory", children=walk(item, relative_base)))
            else:
                nodes.append(FileNode(name=item.name, path=rel, type="file"))
        return nodes

    return walk(repo_path, repo_path)


def read_file(repo_path: Path, rel_path: str) -> str:
    target = safe_join(repo_path, rel_path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return target.read_text(encoding="utf-8", errors="replace")


def write_file(repo_path: Path, rel_path: str, content: str) -> None:
    target = safe_join(repo_path, rel_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def safe_join(repo_path: Path, rel_path: str) -> Path:
    target = (repo_path / rel_path).resolve()
    if repo_path.resolve() not in target.parents and target != repo_path.resolve():
        raise HTTPException(status_code=400, detail="Unsafe file path")
    return target


def iter_code_files(repo_path: Path):
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        root_path = Path(root)
        for file_name in files:
            path = root_path / file_name
            if path.suffix.lower() in TEXT_EXTENSIONS or path.name in {"Dockerfile", "Makefile"}:
                yield path


def search_code(repo_path: Path, query: str, limit: int = 10) -> list[RepoSearchResult]:
    terms = [t.lower() for t in query.split() if t.strip()]
    ranked: list[tuple[int, RepoSearchResult]] = []
    if not terms:
        return []

    for file_path in iter_code_files(repo_path):
        text = file_path.read_text(encoding="utf-8", errors="replace")
        lowered = text.lower()
        score = sum(lowered.count(term) for term in terms)
        if score == 0:
            continue

        first_hit = min((lowered.find(term) for term in terms if term in lowered), default=0)
        start = max(0, first_hit - 120)
        end = min(len(text), first_hit + 240)
        snippet = text[start:end]
        rel = file_path.relative_to(repo_path).as_posix()
        ranked.append((score, RepoSearchResult(path=rel, snippet=snippet)))

    ranked.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in ranked[:limit]]


def collect_project_snapshot(repo_path: Path, max_files: int = 80, max_chars_per_file: int = 4000) -> str:
    chunks: list[str] = []
    for idx, file_path in enumerate(iter_code_files(repo_path)):
        if idx >= max_files:
            break
        rel = file_path.relative_to(repo_path).as_posix()
        content = file_path.read_text(encoding="utf-8", errors="replace")[:max_chars_per_file]
        chunks.append(f"### FILE: {rel}\n{content}")
    return "\n\n".join(chunks)
