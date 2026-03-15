"""LLM Council provider and model defaults (no env vars)."""

from __future__ import annotations

from typing import Literal

Provider = Literal["ollama", "openai", "anthropic", "gemini"]

DEFAULT_MODELS: dict[Provider, str] = {
    "ollama": "llama3.2:3b",
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
    "gemini": "gemini-1.5-flash",
}


def resolve_provider_and_model(
    provider: Provider | None = None,
    model: str | None = None,
) -> tuple[Provider, str]:
    """Resolve (provider, model). None means default: ollama + llama3.2:3b."""
    p: Provider = provider if provider is not None else "ollama"
    m = model if model is not None else DEFAULT_MODELS[p]
    return p, m
