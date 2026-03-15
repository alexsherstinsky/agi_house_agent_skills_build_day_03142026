# AGI House Agent Skills Build Day — LLM Council MCP Tool

A standalone tool that evaluates any artifact — code, design documents, project plans, or any text — using the **LLM Council methodology** (Zhao et al., 2024). Multiple independent reviewer personas analyze your artifact, then their findings are aggregated democratically by consensus strength.

You can use it two ways:
- **From the command line** — `llm-council evaluate <file> --backend <backend>`
- **From within Claude Code** — ask Claude to evaluate something and the MCP tool is called automatically (no API keys needed)

---

## End-to-End Walkthrough

You have an artifact (a design doc, sprint plan, code file, or any text). Here's how to get the Council's critique.

### Step 1: See which reviewer roles the Council recommends

```bash
$ llm-council inspect my_design_doc.md

Detected artifact type: design_doc

Reviewer personas (5):

  1. Systems Architect
     Is the architecture sound? Are the component boundaries clear? Will this scale?
  2. Product Manager
     Does this solve the right problem? Are requirements complete?
  3. Operations Engineer
     Is this operable? What about monitoring, deployment, rollback?
  4. Security Engineer
     What is the threat model? Are auth and data protection addressed?
  5. Domain Expert
     Is the domain model accurate? Are the technical claims correct?
```

The tool auto-detects the artifact type and selects appropriate personas. Run `llm-council personas` to see all available persona sets (code, design_doc, plan, general).

### Step 2: Choose how to run it

**Option A — Single backend (simplest).** All personas use the same LLM:

```bash
llm-council evaluate my_design_doc.md --backend anthropic
```

**Option B — Per-persona config (most powerful).** Assign a different LLM to each role:

```bash
# Generate a starter config with all roles pre-filled
llm-council generate-config my_design_doc.md > my_eval.yaml
```

Edit `my_eval.yaml` — change the `backend` for each role:

```yaml
default_backend: anthropic/claude-sonnet-4-20250514
aggregation_backend: anthropic/claude-opus-4-20250514

personas:
  - role: Systems Architect
    backend: anthropic/claude-opus-4-20250514   # strong reasoning
  - role: Product Manager
    backend: openai/gpt-4o                      # good at product thinking
  - role: Operations Engineer
    backend: anthropic/claude-sonnet-4-20250514
  - role: Security Engineer
    backend: anthropic/claude-sonnet-4-20250514
  - role: Domain Expert
    backend: ollama/llama3.2:3b                 # local, no API key needed
```

Preview the mapping (no LLM calls):

```bash
llm-council inspect my_design_doc.md --config my_eval.yaml
```

**Option C — From within Claude Code (no API keys needed):**

> Use the LLM Council to evaluate the document in `my_design_doc.md`

Claude performs the entire multi-persona review itself using the host LLM.

### Step 3: Review the output

Once you run the evaluation (Option A, B, or C above), you get back:

- Per-persona assessments with chain-of-thought reasoning, each labeled with the backend that produced it
- A consensus summary table: Issue | Consensus | Reviewers | Recommendation
- Overall quality score (1-10) with justification
- Readiness assessment: Ready / Needs Revision / Needs Major Revision
- Data flow notice showing which backends received the artifact

---

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd agi_house_agent_skills_build_day_03142026
uv venv
uv pip install -e ".[dev]"
```

This installs everything: `mcp`, `ollama`, `pyyaml`, `anthropic`, `openai`, `pytest`, and the `llm-council` CLI.

**API keys** (only needed for CLI usage — Claude Code requires none):

| Backend | Env Var | Example |
|---|---|---|
| `anthropic` | `ANTHROPIC_API_KEY` | `export ANTHROPIC_API_KEY="sk-..."` |
| `openai` | `OPENAI_API_KEY` | `export OPENAI_API_KEY="sk-..."` |
| `ollama` | None (local) | Just have Ollama running |

---

## CLI Reference

```
$ llm-council --help

usage: llm-council [-h] {evaluate,inspect,personas,generate-config} ...

Commands:
  evaluate         Evaluate an artifact using the LLM Council
  inspect          Show detected artifact type and recommended personas
  personas         List all available persona sets
  generate-config  Generate a starter YAML config for an artifact type
```

### `llm-council evaluate`

Run a full Council evaluation. Requires `--backend` or `--config`.

```bash
# Single backend — all personas use the same LLM
llm-council evaluate my_code.py --backend anthropic
llm-council evaluate my_code.py --backend openai/gpt-4o
llm-council evaluate my_code.py --backend ollama

# Per-persona config — different LLM per reviewer
llm-council evaluate my_code.py --config configs/mixed_frontier.yaml

# Use a specific model with a backend
llm-council evaluate my_code.py --backend anthropic --model claude-opus-4-20250514

# Pipe text from stdin
cat sprint_plan.md | llm-council evaluate - --backend anthropic

# Preview the prompt without calling any LLM
llm-council evaluate my_code.py --dry-run

# Skip data flow confirmation prompt
llm-council evaluate my_code.py --config configs/mixed_frontier.yaml --yes
```

### `llm-council inspect`

Preview what the Council would do — detected artifact type, recommended personas, and (with `--config`) the persona-backend mapping. No LLM calls.

```bash
llm-council inspect my_code.py
llm-council inspect my_code.py --config my_eval.yaml
```

### `llm-council personas`

List every persona set the tool can select from, grouped by artifact type (code, design_doc, plan, general).

```bash
llm-council personas
```

### `llm-council generate-config`

Generate a starter YAML config with all personas pre-filled. Redirect to a file, edit the backends, and use with `--config`.

```bash
# From an artifact file (auto-detects type)
llm-council generate-config my_doc.md > my_config.yaml

# From a specific artifact type
llm-council generate-config --type design_doc > my_config.yaml
llm-council generate-config --type code > my_config.yaml

# With a different default backend
llm-council generate-config --type plan --default-backend ollama > my_config.yaml
```

---

## Per-Persona Backend Configuration

A YAML config file assigns a different LLM to each reviewer persona. This enables experimenting with which models are best suited for each review perspective. See the Walkthrough above for a complete example.

### Config File Reference

```yaml
default_backend: <backend_id>            # used when a persona has no backend specified
aggregation_backend: <backend_id>        # optional, defaults to default_backend
personas:
  - role: <role_name>                    # must match a built-in role or include perspective
    backend: <backend_id>                # optional, defaults to default_backend
    perspective: "<custom perspective>"  # required only for custom (non-built-in) roles
    temperature: 0.3                     # optional, default 0.3 (lower = more deterministic)
    max_tokens: 4096                     # optional, default 4096
```

### Supported Backends

| Backend ID | Provider | Context Window |
|---|---|---|
| `anthropic/claude-sonnet-4-20250514` | Anthropic | 200k tokens |
| `anthropic/claude-opus-4-20250514` | Anthropic | 200k tokens |
| `openai/gpt-4o` | OpenAI | 128k tokens |
| `openai/gpt-4o-mini` | OpenAI | 128k tokens |
| `ollama/llama3.2:3b` | Ollama (local) | 8k tokens |
| `ollama/mistral` | Ollama (local) | 32k tokens |

You can also use just the provider name (e.g., `anthropic`) to get its default model.

### Ready-to-Use Config Templates

Four config templates are included in `configs/`:

| Config | Backends | API Keys Needed |
|---|---|---|
| `configs/all_claude.yaml` | All Claude Sonnet | `ANTHROPIC_API_KEY` |
| `configs/all_openai.yaml` | All GPT-4o | `OPENAI_API_KEY` |
| `configs/mixed_frontier.yaml` | Claude + GPT-4o + Ollama | Both + Ollama running |
| `configs/local_only.yaml` | All Ollama | None |

For the full multi-backend design rationale, see `Documentation/design_multi_backend_council.md`.

---

## Claude Code Usage (MCP)

If you're working inside Claude Code, the LLM Council is available as an MCP tool automatically (configured in `.mcp.json`). No API keys needed.

Just ask Claude to evaluate something in natural language:

> Use the LLM Council to evaluate this code:
> ```python
> def process(data):
>     query = f"SELECT * FROM users WHERE id = '{data}'"
>     return db.execute(query)
> ```

> Run the LLM Council on the design doc in `Documentation/my_design.md`

> Evaluate our sprint plan using the LLM Council: ...

In host mode (default), Claude performs the entire multi-persona review itself. You can also ask Claude to use a specific backend or config for server-side evaluation.

---

## How It Works

### 1. Artifact Type Detection

The tool scans the input for keyword signals to classify it. When multiple types have signals (e.g., a design doc with embedded code snippets), document-level types take priority: `design_doc > plan > code > general`. Run `llm-council inspect <file>` to see the detected type for any artifact.

| Type | Example Signals |
|---|---|
| `code` | `def `, `class `, `function `, `import `, `const `, `return ` |
| `design_doc` | `## Overview`, `## Requirements`, `## Architecture`, `## API` |
| `plan` | `## Tasks`, `## Timeline`, `## Sprint`, `## Milestones` |
| `general` | Fallback when no strong signal is found |

### 2. Persona Selection

Each artifact type has a tailored set of 5-6 reviewer personas:

- **Code**: Software Engineer, Code Reviewer, Security Engineer, Performance Engineer, QA Engineer
- **Design Doc**: Systems Architect, Product Manager, Operations Engineer, Security Engineer, Domain Expert
- **Plan**: Project Manager, Technical Lead, Risk Analyst, QA Engineer, Stakeholder
- **General**: Target End User, Decision Maker, Domain Expert, Data Integrity Reviewer, Editor, Data Usage Reviewer

### 3. Independent Evaluation

Each persona evaluates the artifact independently using chain-of-thought reasoning — step-by-step analysis before forming a judgment, with specific feedback referencing the artifact.

### 4. Democratic Aggregation

Findings are grouped by how many reviewers flagged them:

| Consensus Level | Threshold | Meaning |
|---|---|---|
| **HIGH PRIORITY** | 3+ reviewers flagged | Critical — must be addressed |
| **MEDIUM PRIORITY** | 2 reviewers flagged | Important — worth addressing |
| **LOWER PRIORITY** | 1 reviewer flagged | Suggestion — consider addressing |

---

## Running Tests

```bash
uv run pytest tests/ -v
```

59 tests covering:
- Artifact type detection (including mixed-content documents)
- Persona selection and prompt generation
- Backend adapters (parsing, creation, context windows, API key validation)
- Config validation (structure, duplicates, custom roles, unknown fields)
- Mode resolution (host, single-backend, per-persona)
- Prompt decomposition (per-persona prompts, aggregation prompts, partial failures)

---

## Local LLM Setup (Ollama)

To use a local LLM instead of a cloud API:

```bash
# Install Ollama and dependencies
./setup.sh

# Verify Ollama is running
./scripts/run_llama.sh "What is 2+2?"

# Use the Council with Ollama
llm-council evaluate my_code.py --backend ollama
```

---

## Collecting Council Responses (Benchmarking)

Full pipeline — collect responses, judge them, and generate the visualization:

```bash
source .venv/bin/activate
python collect_responses.py && python judge_responses.py && python generate_site.py && open docs/index.html
```

Or step by step:

```bash
python collect_responses.py   # → tmp/llm_council_results.md
python judge_responses.py     # → tmp/llm_council_judgments.md
python generate_site.py       # → docs/index.html
open docs/index.html
```

---

## Project Structure

```
├── .mcp.json                  # MCP server configuration for Claude Code
├── pyproject.toml             # Project metadata and dependencies
├── collect_responses.py       # Benchmarking — collect multi-persona responses
├── setup.sh                   # Ollama and dependency installation
├── scripts/
│   └── run_llama.sh           # Run local Ollama model
├── configs/                   # Ready-to-use YAML config templates
│   ├── all_claude.yaml
│   ├── all_openai.yaml
│   ├── mixed_frontier.yaml
│   └── local_only.yaml
├── llm_council_mcp/
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point (llm-council command)
│   ├── server.py              # MCP server — tool registration and handling
│   ├── council.py             # Core logic — type inference, personas, prompt generation
│   ├── backends.py            # LLM backend adapters (Anthropic, OpenAI, Ollama)
│   ├── orchestrator.py        # CouncilOrchestrator — multi-backend evaluation coordinator
│   └── resources/
│       └── llm_council_method.md  # LLM Council methodology reference
├── tests/
│   ├── test_council.py        # Core logic tests (19 tests)
│   ├── test_backends.py       # Backend adapter tests (16 tests)
│   └── test_orchestrator.py   # Orchestrator, config, prompt tests (24 tests)
├── datasets/                  # Evaluation artifacts and Council outputs
│   ├── *.md                   # Source artifacts
│   └── *.llm_council_evaluation.claude.md  # Council evaluation results
└── Documentation/
    ├── hackathon_project_llm_council_skill_and_benchmark.md
    ├── design_multi_backend_council.md  # Multi-backend design doc (reviewed, 10/10)
    └── project_progress_tracker.md
```

### Self-Referential Evaluation

The multi-backend design doc (`Documentation/design_multi_backend_council.md`) was iteratively refined using the LLM Council tool itself — the tool evaluating its own design. Four rounds of Council review improved the score from 8/10 to 10/10, with all findings (HIGH through LOWER) addressed. The evaluation history is preserved in `datasets/`.

## References

- Zhao et al., 2024 — [Language Model Council: Democratically Benchmarking Foundation Models on Highly Subjective Tasks](https://arxiv.org/pdf/2406.08598)
