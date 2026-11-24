"""LLM providers. Swap with LLM_PROVIDER in .env; the rest of the app does not change."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

from ..config import get_settings
from ..schemas import SamplingParameters
from .mock import mock_response


class ProviderError(Exception):
    status_code = 502


class ProviderRateLimited(ProviderError):
    status_code = 429


@dataclass
class Completion:
    text: str
    latency_ms: float


class LLMProvider:
    name = "base"
    model = ""

    def complete(self, step: str, system: str, prompt: str, sampling: SamplingParameters, context: dict) -> Completion:
        raise NotImplementedError


class MockProvider(LLMProvider):
    """Offline provider: returns deterministic, schema-valid JSON so the UI and tests run without a key.
    Its output is template text, NOT model output — never use it for evaluation results."""

    name = "mock"
    model = "mock-template"

    def complete(self, step, system, prompt, sampling, context):
        start = time.perf_counter()
        text = json.dumps(mock_response(step, context))
        return Completion(text, (time.perf_counter() - start) * 1000)


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ProviderError("GEMINI_API_KEY is empty. Add it to backend/.env, or set LLM_PROVIDER=auto for demo mode.")
        from google import genai  # imported lazily so mock mode needs no SDK setup

        self._client = genai.Client(api_key=api_key)
        self.model = model

    def complete(self, step, system, prompt, sampling, context):
        from google.genai import errors, types

        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=sampling.temperature,
            top_p=sampling.top_p,
            top_k=sampling.top_k,
            max_output_tokens=sampling.max_output_tokens,
            seed=sampling.seed,
            response_mime_type="application/json",
        )
        start = time.perf_counter()
        try:
            response = self._client.models.generate_content(model=self.model, contents=prompt, config=config)
        except errors.APIError as exc:
            if getattr(exc, "code", None) == 429:
                raise ProviderRateLimited(
                    "Gemini free-tier quota reached. Wait a minute and try again, or switch GEMINI_MODEL to a Flash-Lite model."
                ) from exc
            raise ProviderError(f"Gemini error: {exc}") from exc
        latency = (time.perf_counter() - start) * 1000
        if not response.text:
            raise ProviderError("Gemini returned an empty response (possibly blocked by safety filters, or Max output tokens is too low).")
        return Completion(response.text, latency)


def get_llm() -> LLMProvider:
    s = get_settings()
    if s.effective_llm == "gemini":
        return GeminiProvider(s.gemini_api_key, s.gemini_model)
    return MockProvider()


def parse_json(text: str) -> dict:
    """Parse model JSON, tolerating ```json fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ProviderError("The model returned incomplete JSON. Try again, or raise Max output tokens in Settings.") from exc
