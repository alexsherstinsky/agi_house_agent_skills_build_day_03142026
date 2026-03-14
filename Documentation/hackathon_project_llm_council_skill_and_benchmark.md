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
- CommandCenter-generated AI insights (agent coaching, manager reports)
- Anonymization tooling already built (Content Discovery MCP Server)

---

## Track 1: The Council as a Standalone MCP Tool

Extract and generalize the LLM Council methodology into a reusable skill that any agent can invoke.

**Inputs:**
- The artifact to evaluate (code, a plan, a design, generated text — anything)
- Evaluation criteria (or let the Council infer them from the artifact type)
- Council configuration (number of personas, persona descriptions, aggregation threshold)

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

1. Gather 5-8 real artifacts from production system (design docs, sprint plans, generated insights)
2. Anonymize using existing tooling
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

| Time | Activity |
|---|---|
| 12:15–1:30 PM | Extract Council logic from workflow server into a standalone MCP tool. Define 3 artifact types it can evaluate (code, design doc, agent plan). |
| 1:30–3:00 PM | Gather 5-8 real artifacts from the codebase. Anonymize them. Run single-pass vs. Council evaluations using Claude. |
| 3:00–4:30 PM | Analyze results. Build comparison table/visualization. Identify where Council caught issues that single-pass missed (and vice versa). |
| 4:30–5:30 PM | Write up findings as a structured report. Identify the optimal persona count. |
| 5:30–7:00 PM | Prepare demo: narrative arc from problem to methodology to tool to experimental results to conclusions. |
| 8:00–9:30 PM | Present. Lead with the problem ("agent outputs are hard to trust"), show the Council approach, present the data. |

---

## Tools & Infrastructure

- **LLM:** Claude (via Claude Code)
- **MCP Framework:** Model Context Protocol for tool definition and composability
- **Anonymization:** Existing Content Discovery MCP Server tooling
- **Source artifacts:** Production design docs, sprint plans, AI-generated insights from ConvoScience platform
