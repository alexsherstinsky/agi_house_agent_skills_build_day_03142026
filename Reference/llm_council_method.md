# LLM Council Method — Cached Methodology Reference

**Source:** Zhao et al., 2024 — "Language Model Council: Democratically Benchmarking
Foundation Models on Highly Subjective Tasks"
**Paper URL:** https://arxiv.org/pdf/2406.08598

---

## Core Concept

The Language Model Council (LMC) is a democratic evaluation framework where multiple
diverse evaluators independently assess a subject using structured reasoning, then their
findings are aggregated democratically to surface high-consensus recommendations.

The original paper uses genuinely different LLMs as council members. Our adaptation
simulates independent personas within a single LLM — the key principles transfer directly.

## Key Principles

1. **Independence** — each council member evaluates independently, without knowledge of
   or influence from other members' assessments. This is the single most important
   principle. Without it, personas converge to a single voice with cosmetic variation.

2. **Diversity** — council members must have distinct professional perspectives relevant
   to the subject being reviewed (e.g., engineering, operations, business, quality,
   security). Diversity prevents blind spots.

3. **Chain-of-thought before judgment** — each member must reason through their evaluation
   step-by-step before stating recommendations. This produces deeper analysis than
   immediate conclusions.

4. **Democratic aggregation** — after all independent evaluations, findings are ranked by
   consensus strength (how many members independently raised the same concern). Strong
   consensus = high priority; novel but valid concerns from a single member are still
   captured at lower priority.

## Process (adapted for single-LLM simulation)

1. **Convene** — simulate 5-7 independent reviewers, each with a named persona and a
   distinct professional lens relevant to the document's domain.

2. **Independent evaluation** — each reviewer reads the document and reasons through their
   assessment step-by-step (chain-of-thought), then states their specific recommendations.
   Each reviewer acts as if they are independent of all other reviewers.

3. **Aggregate** — after all reviews, rank recommendations by consensus strength:
   - **Strong consensus (3+ members)** — HIGH PRIORITY
   - **Moderate consensus (2 members)** — MEDIUM PRIORITY
   - **Novel but valid (1 member)** — LOWER PRIORITY

4. **Output** — suggest changes only; do not modify anything directly.

## Validation Prompt Template

For use in design document and sprint plan validation:

> Review the [DOCUMENT_TYPE] using the LLM Council method (based on Zhao et al., 2024 —
> "Language Model Council"; see https://arxiv.org/pdf/2406.08598 for the full technique):
> simulate 5-7 independent reviewers, each with a distinct professional perspective
> relevant to the subject (e.g., engineering, operations, business, quality, security).
> Each reviewer must reason through their evaluation step-by-step before stating
> recommendations, and must act as if they are independent of all other reviewers. After
> all reviews, aggregate findings democratically — rank recommendations by consensus
> strength (how many reviewers independently raised the same concern). Suggest changes
> only; do not modify anything.

Where `[DOCUMENT_TYPE]` is replaced by the workflow context (e.g., "design document" or
"sprint plan").

## Metrics from the Paper

The paper measures evaluation quality via:
- **Separability** — % of evaluated pairs with non-overlapping confidence intervals
- **Consistency** — agreement rate when evaluation order is swapped
- **Conviction** — % of strong preferences (clear distinction vs. marginal)
- **Agreement** — inter-rater agreement (Cohen's Kappa between judge pairs)
- **Contrarianism** — % disagreement with council majority (flags outlier perspectives)

For our use case, the most relevant metrics are consensus strength (democratic aggregation)
and conviction (are reviewers raising the concern strongly or marginally).
