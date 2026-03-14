"""LLM Council — core logic for multi-persona artifact evaluation.

Infers artifact type, selects appropriate reviewer personas, and generates
structured evaluation prompts based on the LLM Council methodology
(Zhao et al., 2024).
"""

from __future__ import annotations

from pathlib import Path


_METHODOLOGY_PATH: Path = (
    Path(__file__).resolve().parent / "resources" / "llm_council_method.md"
)

# Artifact type detection keywords.
_ARTIFACT_SIGNALS: dict[str, list[str]] = {
    "code": [
        "def ", "class ", "function ", "import ", "const ", "let ", "var ",
        "return ", "if (", "for (", "while (", "try:", "except:", "catch (",
        "public ", "private ", "package ", "func ", "fn ", "impl ",
    ],
    "design_doc": [
        "## Overview", "## Requirements", "## Architecture", "## Design",
        "## Scope", "## Assumptions", "## Constraints", "## Non-functional",
        "## API", "## Data Model", "## System", "## Component",
    ],
    "plan": [
        "## Tasks", "## Milestones", "## Timeline", "## Sprint",
        "## Deliverable", "## Schedule", "## Phase", "## Backlog",
        "## Priority", "## Objective", "## Goal",
    ],
}

# Personas selected per artifact type.
_PERSONAS_BY_TYPE: dict[str, list[dict[str, str]]] = {
    "code": [
        {
            "role": "Software Engineer",
            "perspective": (
                "Is the code correct? Are there bugs, edge cases, or logic errors?"
            ),
        },
        {
            "role": "Code Reviewer",
            "perspective": (
                "Is the code readable and maintainable? Does it follow conventions?"
            ),
        },
        {
            "role": "Security Engineer",
            "perspective": (
                "Are there security vulnerabilities? Input validation issues? "
                "Injection risks?"
            ),
        },
        {
            "role": "Performance Engineer",
            "perspective": (
                "Are there performance concerns? Unnecessary allocations, "
                "O(n^2) where O(n) is possible, missing caching opportunities?"
            ),
        },
        {
            "role": "QA Engineer",
            "perspective": (
                "Is this testable? Are edge cases covered? What test cases are missing?"
            ),
        },
    ],
    "design_doc": [
        {
            "role": "Systems Architect",
            "perspective": (
                "Is the architecture sound? Are the component boundaries clear? "
                "Will this scale?"
            ),
        },
        {
            "role": "Product Manager",
            "perspective": (
                "Does this solve the right problem? Are requirements complete? "
                "Are trade-offs explicit?"
            ),
        },
        {
            "role": "Operations Engineer",
            "perspective": (
                "Is this operable? What about monitoring, deployment, rollback, "
                "and failure modes?"
            ),
        },
        {
            "role": "Security Engineer",
            "perspective": (
                "What is the threat model? Are authentication, authorization, "
                "and data protection addressed?"
            ),
        },
        {
            "role": "Domain Expert",
            "perspective": (
                "Is the domain model accurate? Are the technical claims correct? "
                "Are there gaps in domain coverage?"
            ),
        },
    ],
    "plan": [
        {
            "role": "Project Manager",
            "perspective": (
                "Is the scope realistic? Are dependencies identified? "
                "Are milestones achievable?"
            ),
        },
        {
            "role": "Technical Lead",
            "perspective": (
                "Are the technical tasks well-defined? Are there hidden complexities "
                "or missing tasks?"
            ),
        },
        {
            "role": "Risk Analyst",
            "perspective": (
                "What can go wrong? Are risks identified and mitigated? "
                "What are the critical path items?"
            ),
        },
        {
            "role": "QA Engineer",
            "perspective": (
                "Is testing accounted for? Are acceptance criteria clear? "
                "Is there time for validation?"
            ),
        },
        {
            "role": "Stakeholder",
            "perspective": (
                "Does this deliver value? Are priorities aligned with goals? "
                "Is the timeline acceptable?"
            ),
        },
    ],
    "general": [
        {
            "role": "Target End User",
            "perspective": (
                "Is this useful? Is it practical? Can I apply this immediately?"
            ),
        },
        {
            "role": "Decision Maker",
            "perspective": (
                "Does this address a real problem? Would I act on this "
                "or share it with my team?"
            ),
        },
        {
            "role": "Domain Expert",
            "perspective": (
                "Is the subject matter accurate? Are the technical claims "
                "correctly stated?"
            ),
        },
        {
            "role": "Data Integrity Reviewer",
            "perspective": (
                "Are the claims supported by evidence? Are statistics used fairly?"
            ),
        },
        {
            "role": "Editor",
            "perspective": (
                "Is the writing succinct? Does it flow? Is it clear?"
            ),
        },
        {
            "role": "Data Usage Reviewer",
            "perspective": (
                "Are we implying customer endorsement without consent? "
                "Could any claim be read as a guarantee? "
                "Is the data usage consistent with our agreements?"
            ),
        },
    ],
}


def infer_artifact_type(artifact: str) -> str:
    """Infer the artifact type from its content.

    Counts keyword signals for each type and returns the best match.
    Falls back to "general" if no strong signal is found.
    """
    scores: dict[str, int] = {}
    for artifact_type, signals in _ARTIFACT_SIGNALS.items():
        scores[artifact_type] = sum(1 for s in signals if s in artifact)

    if not scores or max(scores.values()) == 0:
        return "general"

    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return best


def get_personas(artifact_type: str) -> list[dict[str, str]]:
    """Return the reviewer personas for a given artifact type."""
    return _PERSONAS_BY_TYPE.get(artifact_type, _PERSONAS_BY_TYPE["general"])


def build_evaluation_prompt(artifact: str) -> str:
    """Build a complete LLM Council evaluation prompt for the given artifact.

    This is the main entry point. It infers the artifact type, selects
    personas, and returns a structured prompt that instructs the LLM to
    perform multi-persona evaluation with democratic aggregation.
    """
    artifact_type = infer_artifact_type(artifact)
    personas = get_personas(artifact_type)

    # Build persona section.
    persona_lines: list[str] = []
    for idx, persona in enumerate(personas, 1):
        persona_lines.append(
            f"{idx}. **{persona['role']}**\n"
            f"   Perspective: {persona['perspective']}"
        )
    personas_block = "\n".join(persona_lines)

    # Load methodology summary for context.
    methodology_note = ""
    if _METHODOLOGY_PATH.exists():
        methodology_note = (
            "\n\nThis evaluation follows the LLM Council methodology "
            "(Zhao et al., 2024 — \"Language Model Council: Democratically "
            "Benchmarking Foundation Models on Highly Subjective Tasks\"; "
            "see https://arxiv.org/pdf/2406.08598)."
        )

    return f"""\
## LLM Council Evaluation

**Detected artifact type**: {artifact_type}{methodology_note}

---

### Instructions

You are conducting a multi-persona council review. Simulate {len(personas)} \
independent reviewers evaluating the artifact below. This is critical: **each \
reviewer must evaluate independently**, as if they have no knowledge of the \
other reviewers' assessments.

For each reviewer:

1. **State the persona** — name and professional lens.
2. **Think step-by-step** — use chain-of-thought reasoning to analyze the \
artifact from this persona's perspective before forming a judgment.
3. **Provide specific feedback** — quote or reference the relevant part of the \
artifact when flagging an issue. Suggest concrete improvements.
4. **State a recommendation** — what should be changed, and how important is it?

### Reviewer Personas

{personas_block}

### Democratic Aggregation

After all {len(personas)} reviewers have evaluated independently:

1. **Group findings by consensus strength**:
   - **HIGH PRIORITY** (3+ reviewers flagged): Critical issues that must be \
addressed.
   - **MEDIUM PRIORITY** (2 reviewers flagged): Important concerns worth \
addressing.
   - **LOWER PRIORITY** (1 reviewer flagged): Suggestions for consideration.

2. **Present a summary table** with columns: Issue | Consensus | Reviewers | \
Recommendation.

3. **Overall quality score**: Rate 1-10 with a brief justification.

4. **Overall readiness assessment**: Ready / Needs Revision / Needs Major \
Revision.

---

### Artifact to Evaluate

```
{artifact}
```
"""
