from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.schemas.api import ProposedChange
from app.services.diff_service import unified_diff
from app.services.llm_service import llm_service
from app.services.repo_service import collect_project_snapshot, read_file, search_code


@dataclass
class PlannerAgent:
    def run(self, task: str, error_fix_mode: bool = False) -> list[str]:
        if llm_service.available:
            try:
                data = llm_service.complete_json(
                    "You are a senior engineering planner. Return JSON with key 'steps' as an array of concise steps.",
                    f"Task: {task}\nError fix mode: {error_fix_mode}",
                )
                steps = data.get("steps", [])
                if isinstance(steps, list) and steps:
                    return [str(step) for step in steps]
            except Exception:
                pass
        if error_fix_mode:
            return [
                "Parse terminal errors and identify broken files",
                "Edit impacted files to resolve syntax/build issues",
                "Validate that fixes do not break surrounding behavior",
            ]
        return [
            "Identify the most relevant files",
            "Apply focused code changes to satisfy the task",
            "Review for correctness and regression risk",
        ]


@dataclass
class CodeSearchAgent:
    def run(self, repo_path: Path, task: str, focus_paths: list[str]) -> list[dict[str, str]]:
        results = search_code(repo_path, task, limit=12)
        data = [{"path": r.path, "snippet": r.snippet} for r in results]
        for fp in focus_paths:
            try:
                snippet = read_file(repo_path, fp)[:800]
                data.insert(0, {"path": fp, "snippet": snippet})
            except Exception:
                continue

        dedup: dict[str, dict[str, str]] = {}
        for item in data:
            dedup[item["path"]] = item
        return list(dedup.values())[:12]


@dataclass
class CodingAgent:
    def run(
        self,
        repo_path: Path,
        task: str,
        plan: list[str],
        file_context: list[dict[str, str]],
        terminal_logs: str | None,
        error_fix_mode: bool,
    ) -> list[ProposedChange]:
        snapshot = collect_project_snapshot(repo_path, max_files=60, max_chars_per_file=2400)
        context_text = "\n\n".join(
            [f"File: {item['path']}\nSnippet:\n{item['snippet']}" for item in file_context]
        )

        if not llm_service.available:
            return []

        system_prompt = (
            "You are an expert coding agent. Return JSON with 'changes' array. "
            "Each change has: path, new_content, rationale. Always return full new_content for each file. "
            "Do not return markdown fences."
        )

        user_prompt = (
            f"Task: {task}\n"
            f"Error fix mode: {error_fix_mode}\n"
            f"Plan: {plan}\n"
            f"Terminal logs: {terminal_logs or 'N/A'}\n\n"
            f"Relevant snippets:\n{context_text}\n\n"
            f"Project snapshot:\n{snapshot}\n\n"
            "Rules:\n"
            "1) Modify only necessary files.\n"
            "2) Keep code production-ready with no placeholders.\n"
            "3) If no changes are needed, return an empty array."
        )
        try:
            data = llm_service.complete_json(system_prompt, user_prompt)
        except Exception:
            return []
        raw_changes = data.get("changes", [])
        proposed: list[ProposedChange] = []

        if not isinstance(raw_changes, list):
            return proposed

        for item in raw_changes:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path", "")).strip()
            new_content = item.get("new_content", "")
            rationale = str(item.get("rationale", "Updated per task")).strip()
            if not path or not isinstance(new_content, str):
                continue
            try:
                old = read_file(repo_path, path)
            except Exception:
                old = ""
            diff = unified_diff(old, new_content, path)
            proposed.append(
                ProposedChange(
                    path=path,
                    old_content=old,
                    new_content=new_content,
                    diff=diff,
                    rationale=rationale,
                )
            )
        return proposed


@dataclass
class ReviewerAgent:
    def run(self, task: str, plan: list[str], changes: list[ProposedChange]) -> str:
        if not changes:
            if llm_service.available:
                try:
                    return llm_service.complete_text(
                        "You are a strict code reviewer.",
                        f"Task: {task}\nPlan: {plan}\nNo code changes were proposed. Give concise rationale and next actions.",
                    )
                except Exception:
                    pass
            return "No code changes were proposed. Add OPENAI_API_KEY to enable AI-generated edits."

        summary = "\n\n".join([f"Path: {c.path}\nRationale: {c.rationale}\nDiff:\n{c.diff[:4000]}" for c in changes])
        if llm_service.available:
            try:
                return llm_service.complete_text(
                    "You are a strict code reviewer focused on correctness, risk, and tests.",
                    f"Task: {task}\nPlan: {plan}\nProposed changes:\n{summary}\nGive concise review notes.",
                )
            except Exception:
                pass
        return "Generated changes reviewed with local fallback mode. Validate by running build and tests."


class MultiAgentWorkflow:
    def __init__(self) -> None:
        self.planner = PlannerAgent()
        self.search = CodeSearchAgent()
        self.coder = CodingAgent()
        self.reviewer = ReviewerAgent()

    def run(
        self,
        repo_path: Path,
        task: str,
        focus_paths: list[str] | None = None,
        terminal_logs: str | None = None,
        error_fix_mode: bool = False,
    ) -> tuple[list[str], list[ProposedChange], str, list[dict[str, str]]]:
        focus = focus_paths or []
        plan = self.planner.run(task=task, error_fix_mode=error_fix_mode)
        context = self.search.run(repo_path=repo_path, task=task, focus_paths=focus)
        changes = self.coder.run(
            repo_path=repo_path,
            task=task,
            plan=plan,
            file_context=context,
            terminal_logs=terminal_logs,
            error_fix_mode=error_fix_mode,
        )
        review_notes = self.reviewer.run(task=task, plan=plan, changes=changes)
        return plan, changes, review_notes, context


workflow = MultiAgentWorkflow()
