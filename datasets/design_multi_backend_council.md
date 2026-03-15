# Design: Multi-Backend LLM Council

**Author:** Claude (Opus 4.6, via Claude Code)
**Date:** 2026-03-14
**Status:** Draft — awaiting review

> **Self-referential note:** This design document is itself evaluated by the LLM Council tool it proposes to extend. A copy lives in `datasets/design_multi_backend_council.md` alongside its Council evaluation output. This is intentional — we are using the LLM Council process to refine design documents aimed at improving the LLM Council itself.

---

## 1. Overview

Extend the LLM Council tool to support multiple LLM backends, enabling per-persona backend assignment. This allows users to assign the most fitting LLM to each reviewer persona and experiment with different configurations.

---

## 2. Goals

- Support three operating modes: host, single-backend, and per-persona-backend
- Work identically across CLI and MCP
- Preserve the current "host mode" (zero API keys, host LLM does all the work) as the default
- Enable benchmarking the same artifact across different backend configurations

## Non-Goals

- Building adapters for every LLM provider (start with Anthropic, OpenAI, Ollama; extensible)
- Concurrent multi-model evaluation in v1 (sequential is acceptable; concurrency is a future optimization)

---

## 3. Three Operating Modes

### Mode 1: Host (current behavior, default)

The MCP server returns a structured prompt. The host LLM (Claude Code, Cursor, etc.) executes the entire multi-persona evaluation itself.

- **API keys required:** None
- **Cost:** Free (uses host subscription)
- **MCP:** Returns prompt as today
- **CLI:** Not applicable (CLI has no "host" — must specify a backend)

### Mode 2: Single Backend

All personas use the same specified backend. The server makes the LLM calls itself and returns the completed evaluation.

- **API keys required:** One (for the chosen backend)
- **Cost:** API usage for N persona calls + 1 aggregation call
- **MCP:** Server calls the API, returns finished evaluation
- **CLI:** `llm-council evaluate my_doc.md --backend anthropic`

### Mode 3: Per-Persona Backend

Each persona is assigned a specific backend. The server orchestrates all calls and returns the completed evaluation with aggregation.

- **API keys required:** One per distinct backend used
- **Cost:** API usage across all backends
- **MCP:** Server orchestrates, returns finished evaluation
- **CLI:** `llm-council evaluate my_doc.md --config council_config.yaml`

---

## 4. Design Decision: Can "Host" Be a Per-Persona Backend?

This is the key architectural tension.

### The Problem

In per-persona mode, could one persona use "host" while others use API backends? For example:

```yaml
personas:
  - role: Software Engineer
    backend: host          # ← host LLM handles this one
  - role: Security Engineer
    backend: openai/gpt-4  # ← server calls OpenAI
```

### Why This Is Hard

MCP is request-response. The tool call returns one result. To mix host and API personas, the server would need to:

1. Call all API-backed personas itself
2. Return those completed evaluations **plus** a prompt for the host to complete the remaining personas
3. Trust the host LLM to follow the prompt, complete its personas, and aggregate everything

This works but is **fragile** — it depends on the host LLM correctly following instructions to integrate pre-computed results with its own. Different hosts (Claude Code, Cursor, Copilot) may handle this differently.

### Recommendation

**Do not allow mixing "host" with API backends in per-persona mode.** Instead, keep the three modes cleanly separated:

| Mode | Who makes LLM calls | Backends allowed |
|---|---|---|
| Host | Host LLM only | "host" (implicit) |
| Single backend | Server only | Any one API backend |
| Per-persona | Server only | Any mix of API backends |

If a user wants to include the host's own LLM (e.g., Claude) as one of the per-persona backends, they specify it as an API backend (e.g., `anthropic/claude-sonnet-4-20250514`) and provide the API key. It's the same model, just called via API rather than delegated to the host.

### Alternative (Deferred)

If we later want true host-mixing, we could implement a two-phase MCP protocol:
- Phase 1: `llm_council_evaluate` returns partial results + host prompt
- Phase 2: `llm_council_aggregate` accepts host-completed personas and produces final aggregation

This is clean but requires the MCP client to orchestrate two tool calls. Defer to v2.

---

## 5. Backend Adapter Interface

```python
class LLMBackend(Protocol):
    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send a prompt to the LLM and return the text response."""
        ...
```

### Supported Backends (v1)

| Backend ID | Provider | API Key Env Var | Default Model |
|---|---|---|---|
| `anthropic` | Anthropic | `ANTHROPIC_API_KEY` | `claude-sonnet-4-20250514` |
| `openai` | OpenAI | `OPENAI_API_KEY` | `gpt-4o` |
| `ollama` | Ollama (local) | None | `llama3.2:3b` |

Backend IDs support an optional model suffix: `anthropic/claude-opus-4-20250514`, `openai/gpt-4o-mini`, `ollama/mistral`.

---

## 6. Configuration

### Per-Persona Config (YAML)

```yaml
# council_config.yaml
default_backend: anthropic/claude-sonnet-4-20250514

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

**Rules:**
- If `personas` is omitted, auto-infer from artifact type (current behavior)
- If a persona has no `backend`, use `default_backend`
- If `default_backend` is omitted, use `anthropic/claude-sonnet-4-20250514`
- Persona `role` must match a known role for the detected artifact type, or be a custom role with a `perspective` field

### Custom Personas

```yaml
personas:
  - role: Legal Reviewer
    perspective: "Are there IP, licensing, or compliance concerns?"
    backend: anthropic/claude-opus-4-20250514
```

---

## 7. Aggregation

After all per-persona evaluations are collected, a final aggregation call is made to combine them using democratic consensus. This call uses the `default_backend` (or a separately configurable `aggregation_backend`).

```
Input to aggregation LLM:
  - The original artifact
  - All N persona evaluations (verbatim)
  - Aggregation instructions (consensus grouping, summary table, score, readiness)

Output:
  - Consensus summary table
  - Overall quality score
  - Readiness assessment
```

---

## 8. MCP Tool Schema Changes

### Updated `llm_council_evaluate` Input Schema

```json
{
  "type": "object",
  "properties": {
    "artifact": {
      "type": "string",
      "description": "The artifact to evaluate."
    },
    "backend": {
      "type": "string",
      "description": "LLM backend for all personas (e.g., 'anthropic', 'openai/gpt-4o', 'ollama'). Omit for host mode."
    },
    "config": {
      "type": "object",
      "description": "Advanced: per-persona backend configuration.",
      "properties": {
        "default_backend": { "type": "string" },
        "aggregation_backend": { "type": "string" },
        "personas": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "role": { "type": "string" },
              "perspective": { "type": "string" },
              "backend": { "type": "string" }
            },
            "required": ["role"]
          }
        }
      }
    }
  },
  "required": ["artifact"]
}
```

**Mode resolution logic:**
1. If neither `backend` nor `config` is provided → **host mode** (return prompt, current behavior)
2. If `backend` is provided (no `config`) → **single-backend mode** (server calls that backend for all personas)
3. If `config` is provided → **per-persona mode** (server orchestrates per config)

This is backwards-compatible: existing callers that only pass `artifact` get host mode.

---

## 9. CLI Changes

```bash
# Host mode — not applicable for CLI, error with helpful message
llm-council evaluate my_doc.md
# → "Error: CLI requires a backend. Use --backend or --config. See --help."

# Single backend
llm-council evaluate my_doc.md --backend anthropic
llm-council evaluate my_doc.md --backend openai/gpt-4o-mini

# Per-persona config
llm-council evaluate my_doc.md --config council_config.yaml

# Dry-run still works (shows prompt regardless of mode)
llm-council evaluate my_doc.md --dry-run

# New: inspect with config shows persona-backend mapping
llm-council inspect my_doc.md --config council_config.yaml
```

---

## 10. Output Format

The completed evaluation is returned as structured text (markdown), identical in format regardless of mode. Each persona section includes a metadata line identifying the backend used:

```markdown
## Reviewer 1: Software Engineer
**Backend:** anthropic/claude-opus-4-20250514

[evaluation content...]

## Reviewer 2: Security Engineer
**Backend:** openai/gpt-4o

[evaluation content...]

---

## Democratic Aggregation
**Aggregation backend:** anthropic/claude-sonnet-4-20250514

[consensus table, score, readiness...]
```

This metadata is critical for benchmarking — it shows exactly which model produced each persona's evaluation.

---

## 11. API Key Management

API keys are read from environment variables. The server never logs, stores, or transmits keys.

| Backend | Env Var |
|---|---|
| Anthropic | `ANTHROPIC_API_KEY` |
| OpenAI | `OPENAI_API_KEY` |
| Ollama | None (local) |

If a backend is requested but its API key is missing, the server returns a clear error:
```
Error: OPENAI_API_KEY not set. Required for backend 'openai/gpt-4o'.
```

---

## 12. Implementation Plan

### Phase 1: Backend Adapter Layer
- Define `LLMBackend` protocol
- Implement `AnthropicBackend`, `OpenAIBackend`, `OllamaBackend`
- Backend registry: parse `"anthropic/claude-opus-4-20250514"` → adapter + model

### Phase 2: Orchestrator
- New `CouncilOrchestrator` class: takes artifact + persona-backend mapping
- Calls each persona's backend with the per-persona prompt
- Calls aggregation backend with all results
- Returns structured markdown

### Phase 3: MCP Integration
- Update `llm_council_evaluate` schema to accept `backend` and `config`
- Mode resolution logic (host / single / per-persona)
- Host mode remains unchanged (returns prompt)
- Single/per-persona modes use orchestrator, return completed evaluation

### Phase 4: CLI Integration
- Update CLI to accept `--config council_config.yaml`
- Parse YAML config
- Use orchestrator (same code path as MCP)

### Phase 5: Tests
- Unit tests for each backend adapter (mocked API calls)
- Unit tests for mode resolution logic
- Integration test: end-to-end with Ollama (no API key needed)
- Config parsing tests (YAML validation, fallback defaults)

---

## 13. Open Questions

1. **Concurrency:** Should persona evaluations run concurrently (faster, but higher burst API usage) or sequentially (slower, simpler, rate-limit-friendly)? Recommend: sequential in v1, concurrent in v2.

2. **Cost visibility:** Should the tool estimate API cost before running? (e.g., "This evaluation will make 6 API calls across 3 backends. Proceed?")

3. **Caching:** If the same artifact is evaluated multiple times with the same config, should results be cached? Useful for benchmarking stability.

4. **Config templates:** Should we ship default config files (e.g., `configs/all_claude.yaml`, `configs/mixed_frontier.yaml`) as starting points?
