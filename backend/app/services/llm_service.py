from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from openai import OpenAI

from app.core.config import settings


class LLMService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    @property
    def available(self) -> bool:
        return self.client is not None

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if not self.client:
            raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")

        response = self.client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        raw = response.choices[0].message.content or "{}"
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=500, detail=f"LLM returned invalid JSON: {exc}") from exc
        return parsed

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        if not self.client:
            raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""


llm_service = LLMService()
