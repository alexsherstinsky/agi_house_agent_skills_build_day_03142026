"""LLM Council instructions extracted from the Workflow MCP Server.

This is the function that generates multi-persona review instructions
for validation phases. The rest of the workflow server is not needed
for the standalone Council tool.
"""

from __future__ import annotations

from pathlib import Path


# Path to the cached LLM Council methodology reference.
_LLM_COUNCIL_RESOURCE: Path = (
    Path(__file__).resolve().parent / "llm_council_method.md"
)


def _get_llm_council_instructions(document_type: str) -> list[str]:
    """Return LLM Council multi-persona review instructions for validation.

    Args:
        document_type: The type of document being validated
            (e.g., "design document", "sprint plan").

    Returns:
        List of instruction lines to append to validation output.
        Returns an empty list if the resource file is not found.
    """
    if not _LLM_COUNCIL_RESOURCE.exists():
        return []

    return [
        "",
        "**LLM Council Review (Multi-Persona Validation):**",
        "",
        "In addition to the self-evaluation flow above, review this"
        f" {document_type} using the LLM Council method (read"
        ' "https://arxiv.org/pdf/2406.08598" thoroughly in order to understand'
        ' the "Language Model Council" technique in depth):',
        "",
        "1. Simulate 5-7 independent reviewers, each with a distinct professional",
        "   perspective relevant to the subject (e.g., engineering, operations, business,",
        "   quality, security). State each persona's name and lens.",
        "2. Each reviewer must reason through their evaluation step-by-step (chain-of-",
        "   thought) before stating recommendations, and must act as if they are",
        "   independent of all other reviewers.",
        "3. After all reviews, aggregate findings democratically — rank recommendations",
        "   by consensus strength:",
        "   - **Strong consensus (3+ members)** — HIGH PRIORITY",
        "   - **Moderate consensus (2 members)** — MEDIUM PRIORITY",
        "   - **Novel but valid (1 member)** — LOWER PRIORITY",
        "4. Present the aggregated findings to the user. Suggest changes only; do not",
        "   modify anything directly.",
        "",
        f"Full methodology reference: {_LLM_COUNCIL_RESOURCE}",
    ]
