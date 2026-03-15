"""Tests for config validation, mode resolution, and prompt decomposition."""

import pytest

from llm_council_mcp.council import (
    build_aggregation_prompt,
    build_persona_prompt,
)
from llm_council_mcp.orchestrator import (
    CouncilOrchestrator,
    estimate_tokens,
    validate_api_keys,
    validate_config,
)


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------

class TestValidateConfig:
    def test_valid_config_passes(self):
        config = {
            "default_backend": "anthropic",
            "personas": [
                {"role": "Software Engineer"},
                {"role": "Security Engineer"},
            ],
        }
        assert validate_config(config) == []

    def test_empty_personas_array(self):
        config = {"personas": []}
        errors = validate_config(config)
        assert any("non-empty" in e for e in errors)

    def test_persona_missing_role(self):
        config = {"personas": [{"perspective": "test"}]}
        errors = validate_config(config)
        assert any("role" in e for e in errors)

    def test_custom_role_without_perspective(self):
        config = {"personas": [{"role": "Legal Reviewer"}]}
        errors = validate_config(config)
        assert any("perspective" in e for e in errors)

    def test_custom_role_with_perspective_passes(self):
        config = {
            "personas": [
                {"role": "Legal Reviewer", "perspective": "Check for IP issues"},
            ],
        }
        assert validate_config(config) == []

    def test_duplicate_roles(self):
        config = {
            "personas": [
                {"role": "Software Engineer"},
                {"role": "Software Engineer"},
            ],
        }
        errors = validate_config(config)
        assert any("Duplicate" in e for e in errors)

    def test_invalid_backend_id(self):
        config = {
            "personas": [
                {"role": "Software Engineer", "backend": "google/gemini"},
            ],
        }
        errors = validate_config(config)
        assert any("Unknown backend provider" in e for e in errors)

    def test_invalid_default_backend(self):
        config = {
            "default_backend": "google/gemini",
            "personas": [{"role": "Software Engineer"}],
        }
        errors = validate_config(config)
        assert any("Unknown backend provider" in e for e in errors)

    def test_unknown_fields_ignored(self):
        config = {
            "personas": [{"role": "Software Engineer"}],
            "some_future_field": True,
        }
        assert validate_config(config) == []


class TestValidateApiKeys:
    def test_ollama_needs_no_key(self):
        assert validate_api_keys({"ollama/llama3.2:3b"}) == []

    def test_anthropic_missing_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        errors = validate_api_keys({"anthropic/claude-sonnet-4-20250514"})
        assert any("ANTHROPIC_API_KEY" in e for e in errors)

    def test_openai_missing_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        errors = validate_api_keys({"openai/gpt-4o"})
        assert any("OPENAI_API_KEY" in e for e in errors)

    def test_anthropic_with_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        assert validate_api_keys({"anthropic/claude-sonnet-4-20250514"}) == []


# ---------------------------------------------------------------------------
# Mode resolution
# ---------------------------------------------------------------------------

class TestModeResolution:
    def test_host_mode_no_backend_no_config(self):
        # No backend or config means host mode — orchestrator shouldn't be used,
        # but if created with no backend/config it defaults to anthropic.
        orch = CouncilOrchestrator(artifact="test", backend=None, config=None)
        # Should have auto-inferred personas with default backend.
        assert len(orch.persona_assignments) > 0

    def test_single_backend_mode(self):
        orch = CouncilOrchestrator(artifact="def foo(): pass", backend="ollama")
        for pa in orch.persona_assignments:
            assert pa["backend_id"] == "ollama"

    def test_per_persona_mode(self):
        config = {
            "default_backend": "ollama",
            "personas": [
                {"role": "Software Engineer", "backend": "ollama/mistral"},
                {"role": "QA Engineer"},  # should use default
            ],
        }
        orch = CouncilOrchestrator(artifact="def foo(): pass", config=config)
        assert orch.persona_assignments[0]["backend_id"] == "ollama/mistral"
        assert orch.persona_assignments[1]["backend_id"] == "ollama"


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

class TestEstimateTokens:
    def test_basic_estimation(self):
        text = "a" * 400
        assert estimate_tokens(text) == 100

    def test_empty_string(self):
        assert estimate_tokens("") == 0


# ---------------------------------------------------------------------------
# Prompt decomposition
# ---------------------------------------------------------------------------

class TestBuildPersonaPrompt:
    def test_contains_artifact(self):
        artifact = "def hello(): pass"
        persona = {"role": "Software Engineer", "perspective": "Check for bugs."}
        prompt = build_persona_prompt(artifact, persona, "code")
        assert artifact in prompt

    def test_contains_persona_role(self):
        persona = {"role": "Security Engineer", "perspective": "Check for vulns."}
        prompt = build_persona_prompt("some code", persona, "code")
        assert "Security Engineer" in prompt

    def test_contains_artifact_type(self):
        persona = {"role": "Editor", "perspective": "Check clarity."}
        prompt = build_persona_prompt("some text", persona, "design_doc")
        assert "design_doc" in prompt


class TestBuildAggregationPrompt:
    def test_contains_all_persona_evaluations(self):
        evals = [
            {"role": "Engineer", "backend": "anthropic", "status": "success", "evaluation": "Looks good."},
            {"role": "Reviewer", "backend": "openai", "status": "success", "evaluation": "Needs work."},
        ]
        prompt = build_aggregation_prompt("artifact text", evals)
        assert "Looks good." in prompt
        assert "Needs work." in prompt
        assert "artifact text" in prompt

    def test_shows_failed_persona(self):
        evals = [
            {"role": "Engineer", "backend": "anthropic", "status": "success", "evaluation": "Fine."},
            {"role": "Reviewer", "backend": "openai", "status": "error", "error": "timeout"},
        ]
        prompt = build_aggregation_prompt("artifact text", evals)
        assert "FAILED" in prompt
        assert "timeout" in prompt

    def test_partial_note_when_failures(self):
        evals = [
            {"role": "Engineer", "backend": "a", "status": "success", "evaluation": "ok"},
            {"role": "Reviewer", "backend": "b", "status": "error", "error": "err"},
        ]
        prompt = build_aggregation_prompt("artifact", evals)
        assert "1 of 2 personas completed" in prompt
