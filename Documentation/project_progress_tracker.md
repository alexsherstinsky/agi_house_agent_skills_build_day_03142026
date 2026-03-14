# LLM Council Skill — Hackathon Progress Tracker

## Track 1: Standalone MCP Tool (Alex — Tool Building)

### Core Implementation
- ✓ Extract Council logic into standalone module (`llm_council_mcp/council.py`)
- ✓ Artifact type inference (code, design_doc, plan, general)
- ✓ Persona selection per artifact type (5–6 personas each)
- ✓ Chain-of-thought evaluation prompt generation
- ✓ Democratic aggregation instructions (HIGH / MEDIUM / LOWER priority)
- ✓ MCP server with `llm_council_evaluate` tool (`llm_council_mcp/server.py`)
- ✓ MCP configuration (`.mcp.json`)
- ✓ LLM Council methodology reference document (`resources/llm_council_method.md`)

### Testing & Validation
- ✓ End-to-end test: invoke `llm_council_evaluate` on a sample artifact (code with SQL injection — correctly detected as "code", 5 personas selected, full prompt generated)
- ✓ Verify artifact type detection across code, design doc, plan, and general inputs (17 pytest tests)
- ✓ Verify persona selection matches detected artifact type (17 pytest tests)
- ✓ Confirm output structure: per-persona assessments, consensus table, quality score, readiness (17 pytest tests)

### Documentation & Packaging
- ✓ `pyproject.toml` with uv-compatible build system and dev dependencies
- ✓ `README.md` — setup, usage (Claude Code + direct), running tests, how it works, project structure
- ✓ `tests/test_council.py` — 17 unit tests (all passing)

### Refinements & Iteration
- [ ] Tune artifact type detection keywords based on teammate feedback
- [ ] Adjust persona descriptions if evaluations are too generic or off-target
- [ ] Add support for user-configurable Council parameters (future work / stretch)

### Git & Packaging
- [ ] Commit initial implementation
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
