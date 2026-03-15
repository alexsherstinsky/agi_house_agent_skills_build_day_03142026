# The LLM Council — A Composable Skill for Rigorous Agent Output Evaluation

## Tracks: Track 1 (New Agent Skills) + Track 2 (Skill Benchmarking & Evaluation)

## Overview

We are building a reusable, domain-agnostic LLM Council skill that any agent can invoke to evaluate its outputs using multi-persona review with democratic aggregation. We will benchmark this skill against single-pass evaluation on real production artifacts.

---

## Foundation: LLM Council Methodology (Zhao et al., 2024)

Source: "Language Model Council: Democratically Benchmarking Foundation Models on Highly Subjective Tasks"

Core principles:
1. **Independence** — Each evaluator assesses independently without influence from others
2. **Diversity** — Multiple distinct professional perspectives (engineering, operations, business, quality, security)
3. **Chain-of-thought** — Evaluators reason step-by-step before stating recommendations
4. **Democratic aggregation** — Findings ranked by consensus strength:
   - Strong consensus (3+ members) = HIGH PRIORITY
   - Moderate consensus (2 members) = MEDIUM PRIORITY
   - Novel but valid (1 member) = LOWER PRIORITY

## Current State

The LLM Council is currently embedded inside our Workflow MCP Server's validation phases — tightly coupled to design documents and sprint plans. The workflow server manages a 6-phase development lifecycle:

1. design_creation → 2. design_validation → 3. sprint_creation → 4. sprint_validation → 5. implementation → 6. complete

During validation phases, the Council approach is injected as review instructions: simulate 5-7 independent reviewers with distinct professional personas, each using chain-of-thought before stating recommendations, with democratic aggregation of findings.

## Artifacts Available for Benchmarking

- Design documents from production development workflow
- Sprint plans with task breakdowns
- Additional datasets sourced by teammates
- Anonymization tooling available if needed for scrubbing internal details

---

## Track 1: The Council as a Standalone MCP Tool

Extract and generalize the LLM Council methodology into a reusable skill that any agent can invoke.

**Input:**
- The artifact to evaluate (code, a plan, a design, generated text — anything)

The system automatically infers evaluation criteria and Council configuration (persona count, persona types, aggregation thresholds) from the artifact's type and content.

**Outputs:**
- Per-persona chain-of-thought assessments
- Issue list with consensus strength (strong / moderate / novel)
- Overall quality score with confidence interval
- Actionable recommendations ranked by consensus

---

## Track 2: Benchmarking the Council

### Research Question

**Does multi-persona evaluation outperform single-pass evaluation?**

### Experimental Design

1. Gather 5-8 real artifacts (design docs, sprint plans, generated insights, teammate-sourced datasets)
2. Anonymize if needed using existing tooling
3. Evaluate each artifact with:
   - (a) Single-pass LLM review
   - (b) 3-persona Council
   - (c) 5-persona Council
   - (d) 7-persona Council
4. Measure:
   - **Issue discovery rate** — how many substantive issues each method finds
   - **Agreement stability** — how consistent results are across repeated runs
   - **Precision** — do Council-flagged issues hold up under human review?
   - **Marginal value of personas** — does going from 5 to 7 personas add value, or is 3 sufficient?

### Deliverable

Comparative data and analysis showing where Council evaluation catches issues that single-pass misses, the optimal persona count, and guidance for when Council evaluation is worth the additional cost.

---

## Hackathon Day Plan

### Team Roles

- **Tool building (Alex):** Extract Council logic from workflow server into a standalone MCP tool
- **Datasets & benchmarking (3 teammates):** Source datasets, run the Council skill on them, analyze results
- **Presentation (3 teammates):** Prepare and deliver the 3-minute demo to the hackathon audience

### Schedule

| Time | Tool Building | Datasets & Benchmarking |
|---|---|---|
| 12:15–1:30 PM | Extract Council into standalone MCP tool | Source and prepare evaluation datasets |
| 1:30–3:00 PM | Refine tool, support teammates running it | Run single-pass vs. Council evaluations |
| 3:00–4:30 PM | Iterate on tool based on findings | Analyze results, build comparison tables |
| 4:30–5:30 PM | Finalize tool | Write up findings, identify optimal persona count |
| 5:30–7:00 PM | All: Prepare 3-minute demo — problem → methodology → tool → results → conclusions |
| 8:00–9:30 PM | All: Present |

---

## Tools & Infrastructure

- **LLM:** Claude (via Claude Code)
- **MCP Framework:** Model Context Protocol for tool definition and composability
- **Anonymization (optional):** Available for scrubbing internal details if needed
- **Source artifacts:** Production design docs, sprint plans, teammate-sourced datasets

### CouncilMember and --big-models

`collect_responses.py` and `judge_responses.py` use two council lists:

- **Default:** All 3 members use Ollama (`llama3.2:3b`) to save tokens.
- **With `--big-models`:** Same 3 personas, each on a different API (OpenAI, Claude, Gemini).

```bash
python collect_responses.py              # Ollama only
python collect_responses.py --big-models # OpenAI + Claude + Gemini
python judge_responses.py --big-models
```

Install big-model backends: `uv pip install openai anthropic google-generativeai`

---

## Appendix

### Future Work

- **User-configurable Council parameters** — Allow users to override the auto-inferred evaluation criteria, persona count, persona descriptions, and aggregation thresholds for domains where the defaults are a poor fit.
