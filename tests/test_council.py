"""Tests for LLM Council core logic."""

import pytest

from llm_council_mcp.council import (
    build_evaluation_prompt,
    get_personas,
    infer_artifact_type,
)


# ---------------------------------------------------------------------------
# Artifact type detection
# ---------------------------------------------------------------------------

class TestInferArtifactType:
    def test_detects_code_python(self):
        artifact = """\
import os

def process_data(items: list) -> dict:
    result = {}
    for item in items:
        if item.is_valid():
            result[item.key] = item.value
    return result
"""
        assert infer_artifact_type(artifact) == "code"

    def test_detects_code_javascript(self):
        artifact = """\
const fetchData = async (url) => {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error('Failed');
    }
    return response.json();
};
"""
        assert infer_artifact_type(artifact) == "code"

    def test_detects_design_doc(self):
        artifact = """\
# Authentication Service Redesign

## Overview
We are redesigning the authentication service to support OAuth2.

## Requirements
- Support Google and GitHub SSO
- Session tokens must expire after 24 hours

## Architecture
The service will consist of three components...

## API
POST /auth/login
POST /auth/refresh
"""
        assert infer_artifact_type(artifact) == "design_doc"

    def test_detects_plan(self):
        artifact = """\
# Q2 Engineering Plan

## Objective
Migrate the monolith to microservices.

## Timeline
- Week 1-2: Extract user service
- Week 3-4: Extract billing service

## Tasks
- [ ] Set up service mesh
- [ ] Create CI/CD pipelines

## Milestones
1. User service deployed — end of Week 2
2. Billing service deployed — end of Week 4
"""
        assert infer_artifact_type(artifact) == "plan"

    def test_design_doc_with_code_snippets_detected_as_design_doc(self):
        artifact = """\
# System Design Document

## Overview
This service processes incoming events.

## Architecture
The system uses a pub/sub pattern with three components.

## API

```python
class EventProcessor:
    def process(self, event: dict) -> bool:
        if event.get("type") == "critical":
            return self.handle_critical(event)
        return True
```

## Requirements
- Handle 10k events per second
"""
        assert infer_artifact_type(artifact) == "design_doc"

    def test_plan_with_code_snippets_detected_as_plan(self):
        artifact = """\
# Sprint 12 Plan

## Tasks
- [ ] Implement the new parser
- [ ] Update the API client

## Timeline
- Week 1: Parser implementation
- Week 2: Integration

## Milestones
1. Parser passes all tests

Example code to refactor:
```python
def parse(data):
    return json.loads(data)
```
"""
        assert infer_artifact_type(artifact) == "plan"

    def test_non_code_text_with_common_english_words(self):
        """Text containing a single code-like word ('let') should not be classified as code."""
        artifact = """\
# How to Buy a Used Car

## 1. Overview
Buying a used car is one of the largest purchases most people make.

## 3. Where to Buy
If the seller refuses to let you take the car to a mechanic, walk away.
You should always negotiate the total price, not the monthly payment.
"""
        assert infer_artifact_type(artifact) == "general"

    def test_falls_back_to_general(self):
        artifact = "The quick brown fox jumps over the lazy dog."
        assert infer_artifact_type(artifact) == "general"

    def test_empty_string_returns_general(self):
        assert infer_artifact_type("") == "general"


# ---------------------------------------------------------------------------
# Persona selection
# ---------------------------------------------------------------------------

class TestGetPersonas:
    def test_code_personas(self):
        personas = get_personas("code")
        roles = {p["role"] for p in personas}
        assert "Software Engineer" in roles
        assert "Security Engineer" in roles
        assert len(personas) == 5

    def test_design_doc_personas(self):
        personas = get_personas("design_doc")
        roles = {p["role"] for p in personas}
        assert "Systems Architect" in roles
        assert "Product Manager" in roles
        assert len(personas) == 5

    def test_plan_personas(self):
        personas = get_personas("plan")
        roles = {p["role"] for p in personas}
        assert "Project Manager" in roles
        assert "Risk Analyst" in roles
        assert len(personas) == 5

    def test_general_personas(self):
        personas = get_personas("general")
        roles = {p["role"] for p in personas}
        assert "Domain Expert" in roles
        assert "Editor" in roles
        assert len(personas) == 6

    def test_unknown_type_falls_back_to_general(self):
        personas = get_personas("unknown_type")
        assert personas == get_personas("general")


# ---------------------------------------------------------------------------
# Prompt generation
# ---------------------------------------------------------------------------

class TestBuildEvaluationPrompt:
    def test_prompt_contains_artifact(self):
        artifact = "import os\n\ndef hello():\n    return True"
        prompt = build_evaluation_prompt(artifact)
        assert "def hello():" in prompt

    def test_prompt_contains_detected_type(self):
        artifact = "import os\n\ndef hello():\n    return True"
        prompt = build_evaluation_prompt(artifact)
        assert "code" in prompt

    def test_prompt_contains_persona_roles(self):
        artifact = "import os\n\ndef hello():\n    return True"
        prompt = build_evaluation_prompt(artifact)
        assert "Software Engineer" in prompt
        assert "Security Engineer" in prompt

    def test_prompt_contains_aggregation_instructions(self):
        artifact = "Some general text for evaluation."
        prompt = build_evaluation_prompt(artifact)
        assert "HIGH PRIORITY" in prompt
        assert "MEDIUM PRIORITY" in prompt
        assert "LOWER PRIORITY" in prompt

    def test_prompt_contains_scoring_instructions(self):
        artifact = "Some text."
        prompt = build_evaluation_prompt(artifact)
        assert "Overall quality score" in prompt
        assert "Overall readiness assessment" in prompt

    def test_prompt_contains_methodology_reference(self):
        artifact = "Some text."
        prompt = build_evaluation_prompt(artifact)
        assert "Zhao et al., 2024" in prompt
