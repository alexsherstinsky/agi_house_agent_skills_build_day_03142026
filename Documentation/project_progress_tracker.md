# LLM Council Skill — Hackathon Progress Tracker

## Track 1: Standalone MCP Tool (Alex — Tool Building)

### Core Implementation
- ✓ Extract Council logic into standalone module (`llm_council_mcp/council.py`)
- ✓ Artifact type inference (code, design_doc, plan, general) with mixed-content priority (design_doc > plan > code)
- ✓ Persona selection per artifact type (5–6 personas each)
- ✓ Chain-of-thought evaluation prompt generation
- ✓ Democratic aggregation instructions (HIGH / MEDIUM / LOWER priority)
- ✓ MCP server with `llm_council_evaluate` tool (`llm_council_mcp/server.py`)
- ✓ MCP configuration (`.mcp.json`)
- ✓ LLM Council methodology reference document (`resources/llm_council_method.md`)

### Testing & Validation
- ✓ End-to-end test: invoke `llm_council_evaluate` on a sample artifact (code with SQL injection — correctly detected as "code", 5 personas selected, full prompt generated)
- ✓ Verify artifact type detection across code, design doc, plan, and general inputs (19 pytest tests)
- ✓ Verify persona selection matches detected artifact type (19 pytest tests)
- ✓ Confirm output structure: per-persona assessments, consensus table, quality score, readiness (19 pytest tests)
- ✓ Mixed-content artifact detection tests (design doc with code snippets → design_doc, plan with code → plan)

### CLI
- ✓ `llm-council evaluate <file>` — full Council evaluation via LLM (supports `--backend anthropic|ollama|auto`, `--model`, `--dry-run`)
- ✓ `llm-council inspect <file>` — preview detected type and personas without calling an LLM
- ✓ `llm-council personas` — list all available persona sets
- ✓ Stdin support (`-`) for all commands
- ✓ Auto-detection of LLM backend (Anthropic → Ollama fallback)

### Documentation & Packaging
- ✓ `pyproject.toml` with uv-compatible build system, CLI entry point, and dev dependencies (includes anthropic)
- ✓ `README.md` — installation, quick reference, full CLI help, per-persona config, Claude Code usage, how it works, project structure
- ✓ `tests/test_council.py` — 19 unit tests (all passing)

### Self-Referential Council Evaluations
- ✓ Council evaluation of `ai_choreography_design_doc.md` (code personas, score 7/10)
- ✓ Council evaluation of `design_multi_backend_council.md` — 4 rounds of iterative self-improvement:
  - Round 1: 8/10 — 14 findings, all addressed
  - Round 2: 9/10 — 12 findings, all addressed
  - Round 3: 10/10 — 5 findings, all addressed
  - Round 4: 10/10 — 1 finding (status update), addressed. Converged.

### Multi-Backend Design Document
- ✓ `Documentation/design_multi_backend_council.md` — 19-section design doc, status: Reviewed — ready for implementation
- ✓ Three operating modes: host (default, free), single-backend, per-persona
- ✓ Backend adapter interface (Anthropic, OpenAI, Ollama) with context window pre-checks
- ✓ Prompt decomposition (host prompt, per-persona prompt, aggregation prompt)
- ✓ Orchestrator component with structured logging and async design
- ✓ Config validation with prompt injection mitigation
- ✓ Partial failure handling (retry-then-partial, minimum 2 personas)
- ✓ Expected latency, cost model, MCP timeout behavior
- ✓ Data flow notice (CLI confirmation, MCP metadata, dry-run preview)
- ✓ Comprehensive test plan (Phase 5) with edge cases enumerated
- ✓ Config templates planned (all_claude, all_openai, mixed_frontier, local_only)

### Refinements Applied
- ✓ Fixed artifact type detection for mixed-content documents (design_doc > plan > code priority)
- ✓ Removed ConvoScience references from project
- ✓ Resolved merge conflicts in README.md and pyproject.toml

### Git & Packaging
- [ ] Commit current state
- [ ] Push branch and open PR

---

## Track 2: Benchmarking (Teammates — Datasets & Evaluation)

### Dataset Preparation
- [ ] Source 5–8 real artifacts (design docs, sprint plans, generated insights, external datasets)
- [ ] Anonymize artifacts if needed

### Experiment Execution
- [ ] Single-pass LLM review on each artifact
- [ ] 3-persona Council evaluation on each artifact
- [ ] 5-persona Council evaluation on each artifact
- [ ] 7-persona Council evaluation on each artifact

### Analysis
- [ ] Measure issue discovery rate (single-pass vs. Council variants)
- [ ] Measure agreement stability (consistency across repeated runs)
- [ ] Measure precision (do Council-flagged issues hold up under human review?)
- [ ] Determine marginal value of personas (3 vs. 5 vs. 7)
- [ ] Build comparison tables and summary

---

## Presentation (All — 5:30–7:00 PM)

- [ ] Prepare 3-minute demo: problem → methodology → tool → results → conclusions
- [ ] Rehearse and time the presentation
- [ ] Present (8:00–9:30 PM)

---

## Schedule Reference

| Time | Tool Building (Alex) | Datasets & Benchmarking (Teammates) |
|---|---|---|
| 12:15–1:30 PM | Extract Council into standalone MCP tool | Source and prepare evaluation datasets |
| 1:30–3:00 PM | Refine tool, support teammates | Run single-pass vs. Council evaluations |
| 3:00–4:30 PM | Iterate on tool based on findings | Analyze results, build comparison tables |
| 4:30–5:30 PM | Finalize tool | Write up findings, identify optimal persona count |
| 5:30–7:00 PM | All: Prepare 3-minute demo |
| 8:00–9:30 PM | All: Present |
