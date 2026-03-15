"""Tests for backend adapters and registry."""

import pytest

from llm_council_mcp.backends import (
    SUPPORTED_PROVIDERS,
    AnthropicBackend,
    OllamaBackend,
    OpenAIBackend,
    create_backend,
    parse_backend_id,
)


class TestParseBackendId:
    def test_provider_only(self):
        assert parse_backend_id("anthropic") == ("anthropic", "claude-sonnet-4-20250514")

    def test_provider_with_model(self):
        assert parse_backend_id("anthropic/claude-opus-4-20250514") == (
            "anthropic", "claude-opus-4-20250514"
        )

    def test_openai_default(self):
        assert parse_backend_id("openai") == ("openai", "gpt-4o")

    def test_ollama_default(self):
        assert parse_backend_id("ollama") == ("ollama", "llama3.2:3b")

    def test_ollama_with_model(self):
        assert parse_backend_id("ollama/mistral") == ("ollama", "mistral")

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown backend provider"):
            parse_backend_id("google/gemini")

    def test_supported_providers(self):
        assert "anthropic" in SUPPORTED_PROVIDERS
        assert "openai" in SUPPORTED_PROVIDERS
        assert "ollama" in SUPPORTED_PROVIDERS


class TestCreateBackend:
    def test_creates_ollama_backend(self):
        backend = create_backend("ollama/llama3.2:3b")
        assert isinstance(backend, OllamaBackend)
        assert backend.model == "llama3.2:3b"

    def test_anthropic_without_key_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not set"):
            create_backend("anthropic")

    def test_openai_without_key_raises(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
            create_backend("openai")

    def test_anthropic_with_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        backend = create_backend("anthropic/claude-opus-4-20250514")
        assert isinstance(backend, AnthropicBackend)
        assert backend.model == "claude-opus-4-20250514"

    def test_openai_with_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        backend = create_backend("openai/gpt-4o-mini")
        assert isinstance(backend, OpenAIBackend)
        assert backend.model == "gpt-4o-mini"


class TestContextWindow:
    def test_anthropic_context_window(self):
        backend = AnthropicBackend(model="claude-sonnet-4-20250514")
        assert backend.context_window() == 200_000

    def test_openai_context_window(self):
        backend = OpenAIBackend(model="gpt-4o")
        assert backend.context_window() == 128_000

    def test_ollama_context_window(self):
        backend = OllamaBackend(model="llama3.2:3b")
        assert backend.context_window() == 8_192

    def test_unknown_model_gets_default(self):
        backend = OllamaBackend(model="some-unknown-model")
        assert backend.context_window() == 8_192
