# LLM Council MCP Tool

A standalone, domain-agnostic MCP tool that evaluates any artifact using the **LLM Council methodology** (Zhao et al., 2024) — multi-persona independent review with democratic aggregation.

Given an artifact (code, design document, project plan, or any text), the tool:

1. **Infers the artifact type** from its content
2. **Selects reviewer personas** appropriate for that type (5–6 independent reviewers)
3. **Generates a structured evaluation prompt** with chain-of-thought reasoning and democratic aggregation of findings

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# Create virtual environment and install dependencies
uv venv
uv pip install -e ".[dev]"
```

## Using the MCP Tool

### In Claude Code

The `.mcp.json` at the repo root is already configured. Claude Code will automatically discover the `llm_council_evaluate` tool.

To invoke it, ask Claude to evaluate an artifact:

> Evaluate this code using the LLM Council: `<paste code here>`

Or reference a file:

> Use the LLM Council to evaluate the design doc in `Documentation/my_design.md`

### Running the MCP Server Directly

```bash
.venv/bin/python3 -m llm_council_mcp.server
```

The server communicates over stdio using the MCP protocol.

## Running Tests

```bash
uv run pytest tests/ -v
```

This runs unit tests covering:

- **Artifact type detection** — code, design_doc, plan, general
- **Persona selection** — correct personas for each detected type
- **Prompt generation** — output structure includes all expected sections (per-persona assessments, consensus aggregation, quality score, readiness assessment)

## How It Works

### Artifact Type Detection

The tool scans the input for keyword signals to classify it:

| Type | Example Signals |
|---|---|
| `code` | `def `, `class `, `function `, `import `, `const `, `return ` |
| `design_doc` | `## Overview`, `## Requirements`, `## Architecture`, `## API` |
| `plan` | `## Tasks`, `## Timeline`, `## Sprint`, `## Milestones` |
| `general` | Fallback when no strong signal is found |

### Reviewer Personas

Each artifact type has a tailored set of 5–6 reviewer personas. For example:

- **Code**: Software Engineer, Code Reviewer, Security Engineer, Performance Engineer, QA Engineer
- **Design Doc**: Systems Architect, Product Manager, Operations Engineer, Security Engineer, Domain Expert
- **Plan**: Project Manager, Technical Lead, Risk Analyst, QA Engineer, Stakeholder

### Democratic Aggregation

Findings are ranked by consensus strength:

- **HIGH PRIORITY** (3+ reviewers flagged) — Critical issues that must be addressed
- **MEDIUM PRIORITY** (2 reviewers flagged) — Important concerns worth addressing
- **LOWER PRIORITY** (1 reviewer flagged) — Suggestions for consideration

## Project Structure

```
├── .mcp.json                  # MCP server configuration for Claude Code
├── pyproject.toml             # Project metadata and dependencies
├── llm_council_mcp/
│   ├── __init__.py
│   ├── server.py              # MCP server — tool registration and handling
│   ├── council.py             # Core logic — type inference, personas, prompt generation
│   └── resources/
│       └── llm_council_method.md  # LLM Council methodology reference
├── tests/
│   └── test_council.py        # Unit tests
└── Documentation/
    ├── hackathon_project_llm_council_skill_and_benchmark.md
    └── PROGRESS_TRACKER.md
```

## References

- Zhao et al., 2024 — [Language Model Council: Democratically Benchmarking Foundation Models on Highly Subjective Tasks](https://arxiv.org/pdf/2406.08598)
