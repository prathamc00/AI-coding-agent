from __future__ import annotations

import json
from typing import Any

import requests
from fastapi import HTTPException
from openai import OpenAI

from app.core.config import settings


class LLMService:
    def __init__(self) -> None:
        self.use_ollama = settings.ollama_enabled
        
        if self.use_ollama:
            self.ollama_base_url = settings.ollama_base_url.rstrip("/")
            self.requested_model = (settings.ollama_model or "auto").strip()
            self.model = self._resolve_initial_ollama_model()
            self.client = None  # Ollama uses REST API, no client needed
        else:
            self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
            self.model = settings.openai_model

    def _ollama_tags(self) -> list[dict[str, Any]]:
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            response.raise_for_status()
            payload = response.json()
            models = payload.get("models", [])
            return models if isinstance(models, list) else []
        except requests.RequestException:
            return []
        except ValueError:
            return []

    def _model_sort_key(self, model: dict[str, Any]) -> tuple[int, str]:
        size = model.get("size")
        if isinstance(size, int):
            return (size, str(model.get("name", "")))
        details = model.get("details", {})
        parameter_size = details.get("parameter_size") if isinstance(details, dict) else None
        if isinstance(parameter_size, str):
            digits = "".join(ch for ch in parameter_size if (ch.isdigit() or ch == "."))
            try:
                return (int(float(digits) * 1_000_000_000), str(model.get("name", "")))
            except ValueError:
                pass
        return (2**63 - 1, str(model.get("name", "")))

    def _installed_ollama_models(self) -> list[str]:
        models = self._ollama_tags()
        ordered = sorted(models, key=self._model_sort_key)
        return [str(model.get("name", "")).strip() for model in ordered if str(model.get("name", "")).strip()]

    def _resolve_initial_ollama_model(self) -> str:
        installed = self._installed_ollama_models()
        if not installed:
            return self.requested_model or "auto"

        if self.requested_model and self.requested_model.lower() not in {"auto", "smallest"}:
            if self.requested_model in installed:
                return self.requested_model

        return installed[0]

    def _candidate_ollama_models(self, current_model: str | None = None) -> list[str]:
        installed = self._installed_ollama_models()
        if not installed:
            return [self.requested_model] if self.requested_model else []

        candidates = installed[:]
        if self.requested_model and self.requested_model.lower() not in {"auto", "smallest"}:
            candidates = [self.requested_model] + [model for model in installed if model != self.requested_model]

        if current_model:
            candidates = [model for model in candidates if model != current_model]
            candidates.insert(0, current_model)

        deduped: list[str] = []
        for model in candidates:
            if model and model not in deduped:
                deduped.append(model)
        return deduped

    @property
    def available(self) -> bool:
        if self.use_ollama:
            return bool(self._installed_ollama_models())
        else:
            return self.client is not None

    def _complete_ollama(self, system_prompt: str, user_prompt: str, json_format: bool = False, model: str | None = None) -> str:
        """Call Ollama API for text completion with endpoint fallback."""
        chat_url = f"{self.ollama_base_url}/api/chat"
        generate_url = f"{self.ollama_base_url}/api/generate"
        active_model = model or self.model

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        chat_payload: dict[str, Any] = {
            "model": active_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        if json_format:
            chat_payload["format"] = "json"

        try:
            response = requests.post(chat_url, json=chat_payload, timeout=300)
            if response.status_code == 404:
                combined_prompt = f"System:\n{system_prompt}\n\nUser:\n{user_prompt}"
                generate_payload: dict[str, Any] = {
                    "model": active_model,
                    "prompt": combined_prompt,
                    "stream": False,
                    "options": {"temperature": 0.2},
                }
                if json_format:
                    generate_payload["format"] = "json"

                fallback = requests.post(generate_url, json=generate_payload, timeout=300)
                if fallback.status_code >= 400:
                    raise HTTPException(status_code=500, detail=f"Ollama API error ({fallback.status_code}): {fallback.text}")
                data = fallback.json()
                self.model = active_model
                return str(data.get("response", ""))

            if response.status_code >= 400:
                raise HTTPException(status_code=500, detail=f"Ollama API error ({response.status_code}): {response.text}")
            data = response.json()
            self.model = active_model
            return str(data.get("message", {}).get("content", ""))
        except requests.RequestException as exc:
            raise HTTPException(status_code=500, detail=f"Ollama API error: {str(exc)}") from exc

    def _complete_ollama_with_fallbacks(self, system_prompt: str, user_prompt: str, json_format: bool = False) -> str:
        last_error: Exception | None = None
        for candidate in self._candidate_ollama_models(self.model):
            try:
                return self._complete_ollama(system_prompt, user_prompt, json_format=json_format, model=candidate)
            except HTTPException as exc:
                last_error = exc
                detail = str(exc.detail).lower()
                retryable = any(
                    marker in detail
                    for marker in [
                        "not found",
                        "no such model",
                        "model requires more system memory",
                        "cannot allocate memory",
                        "failed to load model",
                    ]
                )
                if not retryable:
                    raise
            except requests.RequestException as exc:
                last_error = exc
                continue

        if last_error:
            raise last_error
        raise HTTPException(status_code=500, detail="Ollama API error: no usable local models found")

    def _extract_json_object(self, text: str) -> dict[str, Any]:
        """Extract a JSON object from raw model text responses."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=500, detail=f"LLM returned invalid JSON: {exc}") from exc

        raise HTTPException(status_code=500, detail="LLM returned invalid JSON: no JSON object found")

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        if not self.available:
            provider = "Ollama" if self.use_ollama else "OpenAI"
            raise HTTPException(status_code=400, detail=f"{provider} is not configured or unavailable")

        if self.use_ollama:
            # For Ollama, request JSON in the prompt itself
            modified_prompt = user_prompt + "\n\nRespond with valid JSON only."
            raw = self._complete_ollama_with_fallbacks(system_prompt, modified_prompt, json_format=True)
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            raw = response.choices[0].message.content or "{}"
        
        return self._extract_json_object(raw)

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        if not self.available:
            provider = "Ollama" if self.use_ollama else "OpenAI"
            raise HTTPException(status_code=400, detail=f"{provider} is not configured or unavailable")
        
        if self.use_ollama:
            return self._complete_ollama_with_fallbacks(system_prompt, user_prompt)
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content or ""


llm_service = LLMService()
