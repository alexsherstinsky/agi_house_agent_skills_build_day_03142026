"""LLM backend adapters for the Council orchestrator.

Each backend implements the LLMBackend protocol — complete() and context_window().
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Protocol

logger = logging.getLogger("llm_council")

# Default generation parameters for evaluation tasks.
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 4096

# Context window sizes (tokens). Stored here as a registry so they're easy to update.
_CONTEXT_WINDOWS: dict[str, int] = {
    "claude-sonnet-4-20250514": 200_000,
    "claude-opus-4-20250514": 200_000,
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "llama3.2:3b": 8_192,
    "mistral": 32_000,
    "gemini-2.0-flash": 1_048_576,
    "gemini-2.5-flash-preview-05-20": 1_048_576,
}

# Default context window when model is not in the registry.
_DEFAULT_CONTEXT_WINDOW = 8_192

# Provider defaults.
_PROVIDER_DEFAULTS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
    "ollama": "llama3.2:3b",
    "gemini": "gemini-2.0-flash",
}

SUPPORTED_PROVIDERS = frozenset(_PROVIDER_DEFAULTS.keys())


class LLMBackend(Protocol):
    """Protocol for LLM backend adapters."""

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        generation_params: dict | None = None,
    ) -> str:
        """Send a prompt to the LLM and return the text response."""
        ...

    def context_window(self) -> int:
        """Return the maximum context window size in tokens."""
        ...


class AnthropicBackend:
    """Backend adapter for the Anthropic (Claude) API."""

    def __init__(self, model: str = "claude-sonnet-4-20250514") -> None:
        self.model = model

    def context_window(self) -> int:
        return _CONTEXT_WINDOWS.get(self.model, _DEFAULT_CONTEXT_WINDOW)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        generation_params: dict | None = None,
    ) -> str:
        import anthropic

        params = generation_params or {}
        temperature = params.get("temperature", DEFAULT_TEMPERATURE)
        max_tokens = params.get("max_tokens", DEFAULT_MAX_TOKENS)

        client = anthropic.Anthropic()
        response = await asyncio.to_thread(
            client.messages.create,
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text


class OpenAIBackend:
    """Backend adapter for the OpenAI API."""

    def __init__(self, model: str = "gpt-4o") -> None:
        self.model = model

    def context_window(self) -> int:
        return _CONTEXT_WINDOWS.get(self.model, _DEFAULT_CONTEXT_WINDOW)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        generation_params: dict | None = None,
    ) -> str:
        import openai

        params = generation_params or {}
        temperature = params.get("temperature", DEFAULT_TEMPERATURE)
        max_tokens = params.get("max_tokens", DEFAULT_MAX_TOKENS)

        client = openai.OpenAI()
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content


class OllamaBackend:
    """Backend adapter for local Ollama models."""

    def __init__(self, model: str = "llama3.2:3b") -> None:
        self.model = model

    def context_window(self) -> int:
        return _CONTEXT_WINDOWS.get(self.model, _DEFAULT_CONTEXT_WINDOW)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        generation_params: dict | None = None,
    ) -> str:
        import ollama

        params = generation_params or {}
        temperature = params.get("temperature", DEFAULT_TEMPERATURE)

        response = await asyncio.to_thread(
            ollama.chat,
            model=self.model,
            options={"temperature": temperature},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response["message"]["content"]


class GeminiBackend:
    """Backend adapter for the Google Gemini API."""

    def __init__(self, model: str = "gemini-2.0-flash") -> None:
        self.model = model

    def context_window(self) -> int:
        return _CONTEXT_WINDOWS.get(self.model, _DEFAULT_CONTEXT_WINDOW)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        generation_params: dict | None = None,
    ) -> str:
        from google import genai

        params = generation_params or {}
        temperature = params.get("temperature", DEFAULT_TEMPERATURE)
        max_tokens = params.get("max_tokens", DEFAULT_MAX_TOKENS)

        client = genai.Client()
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=self.model,
            contents=f"{system_prompt}\n\n{user_prompt}",
            config=genai.types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text


def parse_backend_id(backend_id: str) -> tuple[str, str]:
    """Parse a backend ID like 'anthropic/claude-opus-4-20250514' into (provider, model).

    If no model suffix, uses the provider's default model.
    """
    if "/" in backend_id:
        provider, model = backend_id.split("/", 1)
    else:
        provider = backend_id
        model = _PROVIDER_DEFAULTS.get(provider, "")

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unknown backend provider: '{provider}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_PROVIDERS))}."
        )

    if not model:
        raise ValueError(f"No default model for provider '{provider}'.")

    return provider, model


def create_backend(backend_id: str) -> LLMBackend:
    """Create a backend adapter from a backend ID string."""
    provider, model = parse_backend_id(backend_id)

    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                f"ANTHROPIC_API_KEY not set. Required for backend '{backend_id}'."
            )
        return AnthropicBackend(model=model)
    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                f"OPENAI_API_KEY not set. Required for backend '{backend_id}'."
            )
        return OpenAIBackend(model=model)
    elif provider == "ollama":
        return OllamaBackend(model=model)
    elif provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                f"GEMINI_API_KEY not set. Required for backend '{backend_id}'."
            )
        return GeminiBackend(model=model)
    else:
        raise ValueError(f"Unknown provider: '{provider}'.")
