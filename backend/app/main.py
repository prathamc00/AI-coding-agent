from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.database import Base, engine
from app.models import entities  # noqa: F401
from app.services.llm_service import llm_service

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    provider = "ollama" if settings.ollama_enabled else "openai"
    if settings.ollama_enabled:
        installed_models = llm_service._installed_ollama_models()
        model = installed_models[0] if installed_models else llm_service.model
    else:
        model = settings.openai_model
    return {"status": "ok", "provider": provider, "model": model, "configured_model": settings.ollama_model}
