# AGI House Agent Skills Build Day — LLM Council MCP Tool

A standalone tool that evaluates any artifact — code, design documents, project plans, or any text — using the **LLM Council methodology** (Zhao et al., 2024). Multiple independent reviewer personas analyze your artifact, then their findings are aggregated democratically by consensus strength.

You can use it two ways:
- **From the command line** — `llm-council evaluate <file>`
- **From within Claude Code** — ask Claude to evaluate something and the MCP tool is called automatically

---

## Evaluate a Document (Quick Reference)

Already installed? Here's how to evaluate a document right now.

**From your terminal:**

```bash
# Run the full Council evaluation (calls an LLM)
llm-council evaluate path/to/your_document.md

# Use a specific backend
llm-council evaluate path/to/your_document.md --backend anthropic
llm-council evaluate path/to/your_document.md --backend ollama

# Use a per-persona config (different LLM per reviewer)
llm-council evaluate path/to/your_document.md --config council_config.yaml

# Preview which personas would review it (no LLM call)
llm-council inspect path/to/your_document.md

# Just see the generated prompt (no LLM call)
llm-council evaluate path/to/your_document.md --dry-run
```

**From within Claude Code:**

Open Claude Code in this project directory and type:

> Use the LLM Council to evaluate the document in `path/to/your_document.md`

That's it — Claude reads the file, calls the `llm_council_evaluate` MCP tool, and performs the multi-persona review. No API keys needed.

---

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd agi_house_agent_skills_build_day_03142026
uv venv
uv pip install -e ".[dev]"
```

This installs everything: `mcp`, `ollama`, `anthropic`, `pytest`, and the `llm-council` CLI.

**Note on API keys:** If you use the tool **from within Claude Code**, no API key is needed — your Claude Code subscription covers it. For CLI usage:

| Backend | API Key Required | Env Var |
|---|---|---|
| `anthropic` | Yes | `ANTHROPIC_API_KEY` |
| `openai` | Yes | `OPENAI_API_KEY` |
| `ollama` | No (local) | — |

---

## CLI Usage

After installation, the `llm-council` command is available. Run `llm-council --help` at any time:

```
$ llm-council --help

usage: llm-council [-h] {evaluate,inspect,personas} ...

Evaluate artifacts using the LLM Council methodology — multi-persona review
with democratic aggregation.

positional arguments:
  {evaluate,inspect,personas}
    evaluate            Evaluate an artifact using the LLM Council
    inspect             Show detected artifact type and personas without evaluating
    personas            List all available persona sets
```

### `llm-council evaluate` — Run a Full Council Evaluation

This is the main command. Give it a file (or `-` for stdin), and it calls an LLM to perform a multi-persona Council review.

```bash
# Evaluate a Python file
llm-council evaluate my_code.py

# Evaluate a design document
llm-council evaluate docs/design.md

# Pipe text from stdin
cat sprint_plan.md | llm-council evaluate -

# Choose the LLM backend explicitly
llm-council evaluate my_code.py --backend anthropic
llm-council evaluate my_code.py --backend ollama

# Use a specific model
llm-council evaluate my_code.py --backend anthropic --model claude-sonnet-4-20250514
llm-council evaluate my_code.py --backend ollama --model llama3.2:3b

# Use a per-persona config file
llm-council evaluate my_code.py --config council_config.yaml

# Just print the evaluation prompt without calling an LLM
llm-council evaluate my_code.py --dry-run
```

**What you get back:**

- Per-persona assessments with chain-of-thought reasoning
- A consensus summary table: Issue | Consensus | Reviewers | Recommendation
- Overall quality score (1–10) with justification
- Readiness assessment: Ready / Needs Revision / Needs Major Revision

**Backend auto-detection:** By default (`--backend auto`), the tool tries the Anthropic (Claude) API first, then falls back to a local Ollama model. Use `--backend` to choose explicitly.

### `llm-council inspect` — Preview What the Council Would Do

Shows the detected artifact type and which reviewer personas would be selected, without calling an LLM.

```bash
$ llm-council inspect my_code.py

Detected artifact type: code

Reviewer personas (5):

  1. Software Engineer
     Is the code correct? Are there bugs, edge cases, or logic errors?

  2. Code Reviewer
     Is the code readable and maintainable? Does it follow conventions?

  3. Security Engineer
     Are there security vulnerabilities? Input validation issues? Injection risks?

  4. Performance Engineer
     Are there performance concerns? Unnecessary allocations, O(n^2) where O(n) is possible, missing caching opportunities?

  5. QA Engineer
     Is this testable? Are edge cases covered? What test cases are missing?
```

### `llm-council personas` — List All Available Persona Sets

Shows every persona set the tool can select from, grouped by artifact type.

```bash
$ llm-council personas

=== code (5 personas) ===
  1. Software Engineer ...
  2. Code Reviewer ...
  ...

=== design_doc (5 personas) ===
  1. Systems Architect ...
  ...

=== plan (5 personas) ===
  ...

=== general (6 personas) ===
  ...
```

---

## Per-Persona Backend Configuration

You can assign a different LLM to each reviewer persona using a YAML config file. This enables experimenting with which models are best suited for each review perspective.

```yaml
# council_config.yaml
default_backend: anthropic/claude-sonnet-4-20250514
aggregation_backend: anthropic/claude-opus-4-20250514

personas:
  - role: Software Engineer
    backend: anthropic/claude-opus-4-20250514
  - role: Code Reviewer
    backend: openai/gpt-4o
  - role: Security Engineer
    backend: anthropic/claude-sonnet-4-20250514
  - role: Performance Engineer
    backend: ollama/llama3.2:3b
  - role: QA Engineer
    # no backend specified — uses default_backend
```

Use it from the CLI:

```bash
llm-council evaluate my_doc.md --config council_config.yaml
```

See `Documentation/design_multi_backend_council.md` for the full multi-backend design.

---

## Claude Code Usage (MCP)

If you're working inside Claude Code, the LLM Council is available as an MCP tool automatically (configured in `.mcp.json`).

Just ask Claude to evaluate something in natural language:

> Use the LLM Council to evaluate this code:
> ```python
> def process(data):
>     query = f"SELECT * FROM users WHERE id = '{data}'"
>     return db.execute(query)
> ```

> Run the LLM Council on the design doc in `Documentation/my_design.md`

> Evaluate our sprint plan using the LLM Council: ...

Claude will call the `llm_council_evaluate` tool, which returns the structured evaluation prompt, and then Claude performs the multi-persona review.

---

## How It Works

### 1. Artifact Type Detection

The tool scans the input for keyword signals to classify it. When multiple types have signals (e.g., a design doc with embedded code snippets), document-level types take priority: `design_doc > plan > code > general`.

| Type | Example Signals |
|---|---|
| `code` | `def `, `class `, `function `, `import `, `const `, `return ` |
| `design_doc` | `## Overview`, `## Requirements`, `## Architecture`, `## API` |
| `plan` | `## Tasks`, `## Timeline`, `## Sprint`, `## Milestones` |
| `general` | Fallback when no strong signal is found |

### 2. Persona Selection

Each artifact type has a tailored set of 5–6 reviewer personas:

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

19 unit tests covering artifact type detection (including mixed-content documents), persona selection, and prompt generation.

---

## Local LLM Setup (Ollama)

To use a local LLM instead of the Claude API:

```bash
# Install Ollama and dependencies
./setup.sh

# Verify Ollama is running
./scripts/run_llama.sh "What is 2+2?"

# Then use the Council with Ollama
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
├── llm_council_mcp/
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point (llm-council command)
│   ├── server.py              # MCP server — tool registration and handling
│   ├── council.py             # Core logic — type inference, personas, prompt generation
│   └── resources/
│       └── llm_council_method.md  # LLM Council methodology reference
├── tests/
│   └── test_council.py        # Unit tests (19 tests)
├── datasets/                  # Evaluation artifacts and Council outputs
│   ├── *.md                   # Source artifacts
│   └── *.llm_council_evaluation*.claude.md  # Council evaluation results (per round)
└── Documentation/
    ├── hackathon_project_llm_council_skill_and_benchmark.md
    ├── design_multi_backend_council.md  # Multi-backend design doc (reviewed, 10/10)
    └── project_progress_tracker.md
```

### Self-Referential Evaluation

The multi-backend design doc (`Documentation/design_multi_backend_council.md`) was iteratively refined using the LLM Council tool itself — the tool evaluating its own design. Four rounds of Council review improved the score from 8/10 to 10/10, with all findings (HIGH through LOWER) addressed. The evaluation history is preserved in `datasets/` as a demonstration of the iterative improvement loop.

## References

- Zhao et al., 2024 — [Language Model Council: Democratically Benchmarking Foundation Models on Highly Subjective Tasks](https://arxiv.org/pdf/2406.08598)
