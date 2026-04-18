# AI Coding Agent (Full-Stack)

Production-ready local AI Coding Agent inspired by Cursor/Claude Code lite.

## Tech Stack

- Frontend: Next.js (App Router), TypeScript, Tailwind CSS, React Query, Monaco Editor
- Backend: FastAPI, Pydantic, SQLAlchemy, SQLite, Uvicorn
- Agent Workflow: Planner -> Code Search -> Coding -> Reviewer
- DevOps: Docker, Docker Compose, `.env` support

## Features Implemented

1. Chat with codebase (semantic-ish code search + AI responses)
2. Repository file explorer with Monaco editor
3. AI code generation with proposed edits
4. Diff viewer + accept/reject + apply changes
5. Command runner (`npm install`, `npm run dev`, `npm run build`, `pytest`, `lint`)
6. Chat history persisted in SQLite
7. Multi-agent workflow orchestration
8. Error fix mode (`Fix All Build Errors`) using terminal logs context

## Project Structure

- `frontend/` Next.js client
- `backend/` FastAPI API + agent architecture
- `docker-compose.yml`
- `.env.example`

## Local Setup

### 1. Environment

Copy `.env.example` to `.env` and configure one of the following:

**Option A: OpenAI API (Cloud)**
- `OPENAI_API_KEY=your_key` (required)
- `OPENAI_MODEL=gpt-4o-mini` (optional, defaults to gpt-4o-mini)

**Option B: Ollama (Local)**
- `OLLAMA_ENABLED=true`
- `OLLAMA_BASE_URL=http://localhost:11434` (optional, defaults to localhost:11434)
- `OLLAMA_MODEL=auto` (recommended, automatically picks the smallest installed model)

#### Ollama Setup
1. **Install Ollama**: Download from [ollama.ai](https://ollama.ai)
2. **Pull a model**: 
   ```bash
   ollama pull qwen3.5:4b
   # or any smaller local model you want to use
   ```
3. **Start Ollama**: 
   ```bash
   ollama serve
   ```
   (Ollama runs on `http://localhost:11434` by default)
4. **Set environment**: 
   ```
   OLLAMA_ENABLED=true
   OLLAMA_MODEL=auto
   ```

Optional settings:
- `DATABASE_URL=sqlite:///backend_data/app.db`
- `COMMAND_TIMEOUT_SECONDS=120`
- `NEXT_PUBLIC_API_URL=http://localhost:8000`

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Docker Setup

```bash
# from repo root
cp .env.example .env
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`

## API Endpoints

- `POST /api/upload-repo`
- `POST /api/chat`
- `POST /api/generate-code`
- `POST /api/apply-diff`
- `POST /api/run-command`
- `GET  /api/files`
- `GET  /api/history`

## Notes

- Without `OPENAI_API_KEY`, file browsing and command features still work, while AI generation/chat fall back to minimal behavior.
- Repository uploads support either folder file upload from browser or direct `local_path` (for backend-host local directory).
