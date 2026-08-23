"""LLM abstraction for the summary agent.

Returns an OpenAI-backed LLM when a key is configured, otherwise None so callers
fall back to deterministic template output. Keeping the LLM optional means the
whole multi-agent chat runs offline with no API key.
"""

from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAILLM:
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.model = model
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)

    def complete(self, system: str, user: str) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""


def get_llm() -> OpenAILLM | None:
    """Return an LLM if one is configured, else None (use template fallback)."""
    if settings.llm_provider == "local":
        return None
    if settings.openai_api_key:
        try:
            return OpenAILLM(api_key=settings.openai_api_key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("failed to init OpenAI LLM, using template fallback: %s", exc)
    return None
