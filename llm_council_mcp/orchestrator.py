"""CouncilOrchestrator — coordinates multi-backend Council evaluations.

Instantiated per-request (stateless). Handles config resolution, validation,
per-persona dispatch, retry, aggregation, and output assembly.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any

from llm_council_mcp.backends import (
    SUPPORTED_PROVIDERS,
    create_backend,
    parse_backend_id,
    LLMBackend,
)
from llm_council_mcp.council import (
    build_aggregation_prompt,
    build_persona_prompt,
    get_personas,
    infer_artifact_type,
)

logger = logging.getLogger("llm_council")

# Maximum total evaluation time (seconds). Configurable via env var.
MAX_EVAL_TIME = int(os.environ.get("LLM_COUNCIL_MAX_EVAL_TIME", "600"))

# Per-backend call timeouts (seconds).
_API_TIMEOUT = 120
_OLLAMA_TIMEOUT = 300

# Default retry delay (seconds) when no Retry-After header.
_DEFAULT_RETRY_DELAY = 2


def validate_config(config: dict[str, Any]) -> list[str]:
    """Validate a per-persona config dict. Returns a list of error messages (empty = valid)."""
    errors: list[str] = []

    personas = config.get("personas")
    if personas is not None:
        if not isinstance(personas, list) or len(personas) == 0:
            errors.append("config.personas must be a non-empty array.")
            return errors

        seen_roles: set[str] = set()
        for p in personas:
            role = p.get("role")
            if not role or not isinstance(role, str):
                errors.append("Each persona must have a 'role' field.")
                continue

            if role in seen_roles:
                errors.append(f"Duplicate persona role: '{role}'.")
            seen_roles.add(role)

            # Custom roles need a perspective.
            from llm_council_mcp.council import _PERSONAS_BY_TYPE
            known_roles = {
                persona["role"]
                for personas_list in _PERSONAS_BY_TYPE.values()
                for persona in personas_list
            }
            if role not in known_roles and not p.get("perspective"):
                errors.append(f"Custom role '{role}' requires a 'perspective' field.")

            backend_id = p.get("backend")
            if backend_id:
                try:
                    parse_backend_id(backend_id)
                except ValueError as e:
                    errors.append(str(e))

    for field in ("default_backend", "aggregation_backend"):
        val = config.get(field)
        if val:
            try:
                parse_backend_id(val)
            except ValueError as e:
                errors.append(str(e))

    return errors


def validate_api_keys(backend_ids: set[str]) -> list[str]:
    """Check that required API keys are set for all backends. Returns error messages."""
    errors: list[str] = []
    for bid in backend_ids:
        provider, _ = parse_backend_id(bid)
        if provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
            errors.append(f"ANTHROPIC_API_KEY not set. Required for backend '{bid}'.")
        elif provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
            errors.append(f"OPENAI_API_KEY not set. Required for backend '{bid}'.")
        elif provider == "gemini" and not os.environ.get("GEMINI_API_KEY"):
            errors.append(f"GEMINI_API_KEY not set. Required for backend '{bid}'.")
    return errors


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~1 token per 4 characters."""
    return len(text) // 4


class CouncilOrchestrator:
    """Orchestrates multi-backend Council evaluations."""

    def __init__(
        self,
        artifact: str,
        backend: str | None = None,
        config: dict[str, Any] | None = None,
        progress_callback: Any | None = None,
    ) -> None:
        self.artifact = artifact
        self.backend = backend
        self.config = config or {}
        self.progress_callback = progress_callback

        self.artifact_type = infer_artifact_type(artifact)
        self._resolve_personas_and_backends()

    def _resolve_personas_and_backends(self) -> None:
        """Resolve the persona list and their backend assignments."""
        default_backend = self.config.get("default_backend") or self.backend
        if not default_backend:
            default_backend = "anthropic/claude-sonnet-4-20250514"

        self.aggregation_backend_id = (
            self.config.get("aggregation_backend") or default_backend
        )

        config_personas = self.config.get("personas")
        if config_personas:
            # Use personas from config.
            self.persona_assignments: list[dict[str, Any]] = []
            for p in config_personas:
                role = p["role"]
                perspective = p.get("perspective")
                if not perspective:
                    # Look up built-in perspective.
                    from llm_council_mcp.council import _PERSONAS_BY_TYPE
                    for personas_list in _PERSONAS_BY_TYPE.values():
                        for builtin in personas_list:
                            if builtin["role"] == role:
                                perspective = builtin["perspective"]
                                break
                        if perspective:
                            break

                backend_id = p.get("backend") or default_backend
                gen_params: dict[str, Any] = {}
                if "temperature" in p:
                    gen_params["temperature"] = p["temperature"]
                if "max_tokens" in p:
                    gen_params["max_tokens"] = p["max_tokens"]

                self.persona_assignments.append({
                    "role": role,
                    "perspective": perspective or "",
                    "backend_id": backend_id,
                    "generation_params": gen_params or None,
                })
        else:
            # Auto-infer personas from artifact type.
            personas = get_personas(self.artifact_type)
            self.persona_assignments = [
                {
                    "role": p["role"],
                    "perspective": p["perspective"],
                    "backend_id": default_backend,
                    "generation_params": None,
                }
                for p in personas
            ]

    def _collect_all_backend_ids(self) -> set[str]:
        """Collect all distinct backend IDs needed for this evaluation."""
        ids = {pa["backend_id"] for pa in self.persona_assignments}
        ids.add(self.aggregation_backend_id)
        return ids

    def validate(self) -> list[str]:
        """Run all validation checks. Returns error messages (empty = valid)."""
        errors: list[str] = []

        # Config structure validation.
        if self.config:
            errors.extend(validate_config(self.config))

        if errors:
            return errors

        # API key validation.
        all_backends = self._collect_all_backend_ids()
        errors.extend(validate_api_keys(all_backends))

        if errors:
            return errors

        # Context window pre-check.
        prompt_tokens_est = estimate_tokens(self.artifact) + 500  # artifact + instructions
        exceeded: list[str] = []
        for pa in self.persona_assignments:
            backend = create_backend(pa["backend_id"])
            if prompt_tokens_est > backend.context_window():
                exceeded.append(
                    f"Artifact too large for backend '{pa['backend_id']}' "
                    f"(~{prompt_tokens_est:,} tokens estimated, "
                    f"context limit: {backend.context_window():,})."
                )
        if exceeded:
            errors.extend(exceeded)
            errors.append("Use a backend with a larger context window, or shorten the artifact.")

        return errors

    async def _call_persona(
        self, index: int, total: int, assignment: dict[str, Any]
    ) -> dict[str, Any]:
        """Call a single persona's backend and return the result dict."""
        role = assignment["role"]
        backend_id = assignment["backend_id"]
        persona = {"role": role, "perspective": assignment["perspective"]}
        prompt = build_persona_prompt(self.artifact, persona, self.artifact_type)

        provider, _ = parse_backend_id(backend_id)
        timeout = _OLLAMA_TIMEOUT if provider == "ollama" else _API_TIMEOUT

        backend = create_backend(backend_id)
        system_prompt = (
            f"You are {role}. Evaluate the artifact from your professional perspective. "
            f"Be thorough and specific."
        )

        start = time.time()
        last_error = None

        for attempt in range(2):  # 1 try + 1 retry
            try:
                result = await asyncio.wait_for(
                    backend.complete(
                        system_prompt, prompt, assignment.get("generation_params")
                    ),
                    timeout=timeout,
                )
                latency_ms = int((time.time() - start) * 1000)

                log_entry = {
                    "event": "persona_call",
                    "persona": role,
                    "backend": backend_id,
                    "latency_ms": latency_ms,
                    "status": "success",
                    "input_tokens_est": estimate_tokens(prompt),
                    "output_tokens": estimate_tokens(result),
                }
                logger.info(json.dumps(log_entry))

                if self.progress_callback:
                    self.progress_callback(index, total, role, backend_id, latency_ms)

                return {
                    "role": role,
                    "backend": backend_id,
                    "status": "success",
                    "evaluation": result,
                    "latency_ms": latency_ms,
                }

            except Exception as e:
                last_error = str(e)
                if attempt == 0:
                    # Retry logic: respect Retry-After if available.
                    retry_after = _DEFAULT_RETRY_DELAY
                    if hasattr(e, "response") and hasattr(e.response, "headers"):
                        retry_after = int(
                            e.response.headers.get("Retry-After", _DEFAULT_RETRY_DELAY)
                        )
                    log_entry = {
                        "event": "persona_call",
                        "persona": role,
                        "backend": backend_id,
                        "status": "retrying",
                        "error_type": type(e).__name__,
                        "error_message": last_error,
                    }
                    logger.warning(json.dumps(log_entry))
                    await asyncio.sleep(retry_after)

        # Both attempts failed.
        latency_ms = int((time.time() - start) * 1000)
        log_entry = {
            "event": "persona_call",
            "persona": role,
            "backend": backend_id,
            "latency_ms": latency_ms,
            "status": "error",
            "error_type": type(last_error).__name__,
            "error_message": last_error,
        }
        logger.error(json.dumps(log_entry))

        return {
            "role": role,
            "backend": backend_id,
            "status": "error",
            "error": last_error,
            "latency_ms": latency_ms,
        }

    async def run(self) -> str:
        """Run the full Council evaluation and return structured markdown output."""
        # Validation.
        errors = self.validate()
        if errors:
            return "Error:\n" + "\n".join(f"- {e}" for e in errors)

        total = len(self.persona_assignments)
        total_steps = total + 1  # personas + aggregation
        start_time = time.time()

        # Dispatch persona calls sequentially.
        persona_results: list[dict[str, Any]] = []
        for i, assignment in enumerate(self.persona_assignments):
            # Check total time budget.
            elapsed = time.time() - start_time
            if elapsed > MAX_EVAL_TIME:
                logger.error(
                    json.dumps({
                        "event": "timeout",
                        "elapsed_s": int(elapsed),
                        "max_s": MAX_EVAL_TIME,
                        "completed": len(persona_results),
                        "total": total,
                    })
                )
                break

            result = await self._call_persona(i + 1, total_steps, assignment)
            persona_results.append(result)

        # Check minimum viable evaluation.
        succeeded = [r for r in persona_results if r["status"] == "success"]
        if len(succeeded) < 2:
            failed_details = [
                f"- {r['role']} ({r['backend']}): {r.get('error', 'unknown')}"
                for r in persona_results if r["status"] != "success"
            ]
            return (
                "Error: Evaluation failed — fewer than 2 personas succeeded. "
                "Democratic aggregation requires at least 2 reviewers.\n\n"
                "Failed personas:\n" + "\n".join(failed_details)
            )

        # Aggregation.
        aggregation_prompt = build_aggregation_prompt(self.artifact, persona_results)
        agg_backend = create_backend(self.aggregation_backend_id)
        agg_system = "You are aggregating independent reviewer evaluations. Be precise and fair."

        agg_start = time.time()
        try:
            provider, _ = parse_backend_id(self.aggregation_backend_id)
            timeout = _OLLAMA_TIMEOUT if provider == "ollama" else _API_TIMEOUT
            aggregation_result = await asyncio.wait_for(
                agg_backend.complete(agg_system, aggregation_prompt),
                timeout=timeout,
            )
            agg_latency = int((time.time() - agg_start) * 1000)
            logger.info(json.dumps({
                "event": "aggregation_call",
                "backend": self.aggregation_backend_id,
                "latency_ms": agg_latency,
                "status": "success",
            }))
        except Exception as e:
            agg_latency = int((time.time() - agg_start) * 1000)
            logger.error(json.dumps({
                "event": "aggregation_call",
                "backend": self.aggregation_backend_id,
                "latency_ms": agg_latency,
                "status": "error",
                "error_message": str(e),
            }))
            aggregation_result = (
                "Aggregation failed: " + str(e) + "\n\n"
                "Individual persona evaluations are shown above."
            )

        if self.progress_callback:
            self.progress_callback(
                total_steps, total_steps, "Aggregation",
                self.aggregation_backend_id, agg_latency,
            )

        # Assemble output.
        total_time = time.time() - start_time
        return self._assemble_output(persona_results, aggregation_result, total_time)

    def _assemble_output(
        self,
        persona_results: list[dict[str, Any]],
        aggregation_result: str,
        total_time: float,
    ) -> str:
        """Assemble the final structured markdown output."""
        # Data flow notice.
        backends_used = set()
        for r in persona_results:
            provider, _ = parse_backend_id(r["backend"])
            label = "local" if provider == "ollama" else "external"
            backends_used.add(f"{r['backend']} ({label})")
        agg_provider, _ = parse_backend_id(self.aggregation_backend_id)
        agg_label = "local" if agg_provider == "ollama" else "external"
        backends_used.add(f"{self.aggregation_backend_id} ({agg_label})")

        data_flow = (
            "> **Data flow:** This evaluation sent the artifact to the following backends: "
            + ", ".join(sorted(backends_used)) + ".\n"
        )

        # Per-persona sections.
        sections: list[str] = []
        for i, r in enumerate(persona_results, 1):
            if r["status"] == "success":
                sections.append(
                    f"## Reviewer {i}: {r['role']}\n"
                    f"**Backend:** {r['backend']}\n\n"
                    f"{r['evaluation']}"
                )
            else:
                sections.append(
                    f"## Reviewer {i}: {r['role']}\n"
                    f"**Backend:** {r['backend']}\n"
                    f"**Status:** FAILED — {r.get('error', 'unknown error')}"
                )

        persona_block = "\n\n---\n\n".join(sections)

        total_s = int(total_time)
        minutes = total_s // 60
        seconds = total_s % 60
        time_str = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"

        return (
            f"# LLM Council Evaluation\n\n"
            f"**Detected artifact type:** {self.artifact_type}\n"
            f"**Total evaluation time:** {time_str}\n\n"
            f"{data_flow}\n"
            f"---\n\n"
            f"{persona_block}\n\n"
            f"---\n\n"
            f"## Democratic Aggregation\n"
            f"**Aggregation backend:** {self.aggregation_backend_id}\n\n"
            f"{aggregation_result}"
        )
