# AGI House Agent Skills Build Day — LLM Council MCP Tool

A standalone MCP tool that evaluates any artifact — code, design documents, project plans, or any text — using the **LLM Council methodology** (Zhao et al., 2024). Multiple independent reviewer personas analyze your artifact, then their findings are aggregated democratically by consensus strength.

## Quick Start

```bash
git clone <repo-url>
cd agi_house_agent_skills_build_day_03142026
uv venv
uv pip install -e ".[dev]"
```

Then open the project in Claude Code — the `llm_council_evaluate` tool is automatically available via `.mcp.json`.

---

## How to Use the LLM Council Tool

### What It Does

You give it an artifact (any text). The tool:

1. **Detects the artifact type** — is it code? a design doc? a project plan? something else?
2. **Selects 5–6 reviewer personas** tailored to that type
3. **Generates a structured evaluation** where each persona independently reviews the artifact using chain-of-thought reasoning
4. **Aggregates findings democratically** — issues flagged by 3+ reviewers are HIGH PRIORITY, 2 reviewers = MEDIUM, 1 = LOWER

### What You Get Back

The tool returns a structured evaluation containing:

- **Per-persona assessments** — each reviewer's step-by-step analysis, specific feedback (with quotes from the artifact), and recommendations
- **Consensus summary table** — every issue ranked by how many reviewers flagged it, with columns: Issue | Consensus | Reviewers | Recommendation
- **Overall quality score** — 1–10 with justification
- **Readiness assessment** — Ready / Needs Revision / Needs Major Revision

### Using It in Claude Code

The `.mcp.json` is already configured. Just ask Claude to evaluate something:

**Evaluate inline text:**
> Use the LLM Council to evaluate this code:
> ```python
> def process(data):
>     query = f"SELECT * FROM users WHERE id = '{data}'"
>     return db.execute(query)
> ```

**Evaluate a file:**
> Use the LLM Council to evaluate the design doc in `Documentation/my_design.md`

**Evaluate a plan:**
> Run the LLM Council on our sprint plan below: ...

You don't need to specify the artifact type or personas — the tool infers everything automatically.

### Using It Programmatically

You can also call the core logic directly from Python:

```python
from llm_council_mcp.council import build_evaluation_prompt, infer_artifact_type

artifact = open("my_design_doc.md").read()

# See what type was detected
print(infer_artifact_type(artifact))  # e.g., "design_doc"

# Get the full evaluation prompt
prompt = build_evaluation_prompt(artifact)
print(prompt)
```

### Running the MCP Server Directly

```bash
.venv/bin/python3 -m llm_council_mcp.server
```

The server communicates over stdio using the MCP protocol. Any MCP-compatible client can connect to it.

---

## Artifact Types and Personas

The tool automatically selects reviewer personas based on what it detects:

### Code
Detected by: `def `, `class `, `function `, `import `, `const `, `return `, `try:`, `catch (`, etc.

| Persona | What They Look For |
|---|---|
| Software Engineer | Correctness, bugs, edge cases, logic errors |
| Code Reviewer | Readability, maintainability, conventions |
| Security Engineer | Vulnerabilities, injection risks, input validation |
| Performance Engineer | Unnecessary allocations, algorithmic complexity, caching |
| QA Engineer | Testability, edge case coverage, missing test cases |

### Design Documents
Detected by: `## Overview`, `## Requirements`, `## Architecture`, `## API`, `## Data Model`, etc.

| Persona | What They Look For |
|---|---|
| Systems Architect | Architecture soundness, component boundaries, scalability |
| Product Manager | Problem-solution fit, requirements completeness, trade-offs |
| Operations Engineer | Operability, monitoring, deployment, failure modes |
| Security Engineer | Threat model, authentication, authorization, data protection |
| Domain Expert | Domain model accuracy, technical claims, coverage gaps |

### Project Plans
Detected by: `## Tasks`, `## Timeline`, `## Sprint`, `## Milestones`, `## Deliverable`, etc.

| Persona | What They Look For |
|---|---|
| Project Manager | Scope realism, dependencies, milestone achievability |
| Technical Lead | Task definition quality, hidden complexities, missing tasks |
| Risk Analyst | What can go wrong, risk identification, critical path |
| QA Engineer | Testing accounted for, acceptance criteria, validation time |
| Stakeholder | Value delivery, priority alignment, timeline acceptability |

### General Text (Fallback)
Used when no strong artifact type signal is found.

| Persona | What They Look For |
|---|---|
| Target End User | Usefulness, practicality, immediate applicability |
| Decision Maker | Problem relevance, actionability |
| Domain Expert | Subject matter accuracy, correctness of claims |
| Data Integrity Reviewer | Evidence support, fair use of statistics |
| Editor | Clarity, flow, conciseness |
| Data Usage Reviewer | Consent implications, guarantees, data usage consistency |

---

## Democratic Aggregation

After all reviewers evaluate independently, findings are grouped by consensus:

| Consensus Level | Threshold | Meaning |
|---|---|---|
| **HIGH PRIORITY** | 3+ reviewers flagged | Critical — must be addressed |
| **MEDIUM PRIORITY** | 2 reviewers flagged | Important — worth addressing |
| **LOWER PRIORITY** | 1 reviewer flagged | Suggestion — consider addressing |

This ensures that issues with broad agreement surface first, while unique insights from individual reviewers are still captured.

---

## Running Tests

```bash
uv run pytest tests/ -v
```

17 unit tests covering artifact type detection, persona selection, and prompt generation.

---

## Local LLM (Ollama)

Separately from the LLM Council tool, this repo includes scripts for running a local LLM:

```bash
# Install Ollama and dependencies
./setup.sh

# Interactive chat with llama3.2:3b
./scripts/run_llama.sh

# One-shot prompt
./scripts/run_llama.sh "What is 2+2?"

# Run prompt variants
source .venv/bin/activate
python main.py
```

---

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
    └── project_progress_tracker.md
```

## References

- Zhao et al., 2024 — [Language Model Council: Democratically Benchmarking Foundation Models on Highly Subjective Tasks](https://arxiv.org/pdf/2406.08598)
