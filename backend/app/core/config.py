from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "backend_data"
REPOS_DIR = DATA_DIR / "repos"
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPOS_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseModel):
    app_name: str = "AI Coding Agent"
    # OpenAI Configuration
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    # Ollama Configuration
    ollama_enabled: bool = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama2")
    # Database & General
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'app.db').absolute().as_posix()}")
    command_timeout_seconds: int = int(os.getenv("COMMAND_TIMEOUT_SECONDS", "120"))


settings = Settings()
