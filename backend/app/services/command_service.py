from __future__ import annotations

import subprocess
from pathlib import Path

from app.core.config import settings

ALLOWED_COMMANDS = {
    "npm install": ["npm", "install"],
    "npm run dev": ["npm", "run", "dev"],
    "npm run build": ["npm", "run", "build"],
    "pytest": ["pytest"],
    "lint": ["npm", "run", "lint"],
}


def run_project_command(repo_path: Path, command: str) -> tuple[str, str]:
    if command not in ALLOWED_COMMANDS:
        return "failed", f"Command not allowed: {command}"

    args = ALLOWED_COMMANDS[command]
    try:
        proc = subprocess.run(
            args,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=settings.command_timeout_seconds,
            shell=False,
        )
    except FileNotFoundError:
        return "failed", f"Executable not found for command: {command}"
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + "\n" + (exc.stderr or "")
        return "failed", f"Command timed out after {settings.command_timeout_seconds}s\n{output}".strip()

    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    status = "success" if proc.returncode == 0 else "failed"
    return status, output.strip()
