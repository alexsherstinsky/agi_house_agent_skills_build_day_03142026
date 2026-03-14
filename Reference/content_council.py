"""LMC (Language Model Council) validation prompts for content review.

Generates structured prompts that instruct an LLM to simulate independent
reviewer personas evaluating an artifact. The actual evaluation is
performed by the LLM in the conversation — this module only generates the
instructions.

Persona inference guidance:
    The personas below are generic examples. A general-purpose Council tool
    should infer appropriate personas from the artifact's type and content.
    For artifacts touching regulated, contractual, or policy-sensitive
    domains, the system should consider adding a Legal/Compliance persona
    (e.g., "Are there regulatory risks? Could any statement create
    liability? Are contractual obligations met?").
"""

from __future__ import annotations


CONTENT_PERSONAS: dict[str, dict[str, str]] = {
    "end_user": {
        "role": "Target End User",
        "perspective": "Is this useful? Is it practical? Can I apply this immediately?",
    },
    "decision_maker": {
        "role": "Decision Maker",
        "perspective": "Does this address a real problem? Would I act on this or share it with my team?",
    },
    "content_strategist": {
        "role": "Content Strategist",
        "perspective": "Is this engaging? Does the narrative hold attention? Is the hook strong?",
    },
    "domain_expert": {
        "role": "Domain Expert",
        "perspective": "Is the subject matter accurate? Are the technical claims correctly stated?",
    },
    "data_reviewer": {
        "role": "Data Integrity Reviewer",
        "perspective": "Are the claims supported by evidence? Are statistics used fairly?",
    },
    "editor": {
        "role": "Editor",
        "perspective": "Is the writing succinct? Does it flow? Is it preachy?",
    },
    "data_usage_reviewer": {
        "role": "Data Usage Reviewer",
        "perspective": (
            "Are we implying customer endorsement without consent? "
            "Could any claim be read as a guarantee? "
            "Is the data usage consistent with our agreements?"
        ),
    },
}

# Artifact-type-specific guidance.
_ARTIFACT_TYPE_GUIDANCE: dict[str, str] = {
    "code": (
        "This is source code. Evaluate for correctness, readability, "
        "maintainability, and adherence to best practices."
    ),
    "design_doc": (
        "This is a design document. Evaluate for completeness, feasibility, "
        "clarity of requirements, and identification of risks."
    ),
    "plan": (
        "This is a project plan. Evaluate for clarity, risk coverage, "
        "realistic scoping, and actionability of tasks."
    ),
}


def get_validation_prompts(artifact_type: str) -> str:
    """Generate LMC validation instructions for an artifact.

    Returns a structured prompt that the LLM follows to simulate
    independent reviewers evaluating the artifact.

    Args:
        artifact_type: One of "code", "design_doc", "plan".

    Returns:
        A formatted instruction string for the LLM to follow.

    Raises:
        ValueError: If artifact_type is not recognized.
    """
    if artifact_type not in _ARTIFACT_TYPE_GUIDANCE:
        valid: str = ", ".join(sorted(_ARTIFACT_TYPE_GUIDANCE))
        raise ValueError(
            f"Unknown artifact type: {artifact_type!r}. Valid types: {valid}"
        )

    guidance: str = _ARTIFACT_TYPE_GUIDANCE[artifact_type]

    # Build persona section.
    persona_lines: list[str] = []
    for idx, (key, persona) in enumerate(CONTENT_PERSONAS.items(), 1):
        persona_lines.append(
            f"{idx}. **{persona['role']}** ({key})\n"
            f"   Perspective: {persona['perspective']}"
        )
    personas_block: str = "\n".join(persona_lines)

    return f"""\
## LMC Artifact Validation

**Artifact type**: {artifact_type}
**Evaluation guidance**: {guidance}

### Instructions

Simulate {len(CONTENT_PERSONAS)} independent reviewers evaluating the artifact below. For each reviewer:

1. **Think independently** — Use chain-of-thought reasoning before forming a judgment. Do not let one reviewer's opinion influence another.
2. **Evaluate from their specific perspective** — Each reviewer has a distinct role and set of concerns.
3. **Provide specific feedback** — Quote the relevant passage when flagging an issue. Suggest concrete improvements.

### Reviewers

{personas_block}

### Aggregation

After all {len(CONTENT_PERSONAS)} reviewers have evaluated independently:

1. **Group findings by consensus strength**:
   - **HIGH** (3+ reviewers flagged): Critical issues that must be addressed.
   - **MEDIUM** (2 reviewers flagged): Important concerns worth discussing.
   - **LOWER** (1 reviewer flagged): Minor suggestions for consideration.

2. **Present a summary table** with columns: Issue, Consensus, Reviewers, Suggestion.

3. **Give an overall readiness assessment**: Ready / Needs Revision / Needs Major Revision.
"""
