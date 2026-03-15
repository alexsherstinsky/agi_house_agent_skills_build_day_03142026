#!/usr/bin/env python3
"""LLM Council CLI.

Evaluate any artifact from the command line using the LLM Council methodology.

Usage:
    # Evaluate a file (single backend)
    llm-council evaluate my_code.py --backend anthropic

    # Evaluate with per-persona config
    llm-council evaluate my_code.py --config council_config.yaml

    # Pipe text in
    cat design_doc.md | llm-council evaluate - --backend ollama

    # Just see the generated prompt (no LLM call)
    llm-council evaluate my_code.py --dry-run

    # Show what artifact type and personas would be selected
    llm-council inspect my_code.py

    # List all available persona sets
    llm-council personas

Run `llm-council --help` for full usage.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import yaml

from llm_council_mcp.council import (
    _PERSONAS_BY_TYPE,
    build_evaluation_prompt,
    get_personas,
    infer_artifact_type,
)


def _read_artifact(source: str) -> str:
    """Read artifact text from a file path or stdin ('-')."""
    if source == "-":
        text = sys.stdin.read()
        if not text.strip():
            print("Error: no input received on stdin.", file=sys.stderr)
            sys.exit(1)
        return text

    path = Path(source)
    if not path.exists():
        print(f"Error: file not found: {source}", file=sys.stderr)
        sys.exit(1)
    return path.read_text()


def _load_config(config_path: str) -> dict:
    """Load a YAML config file."""
    path = Path(config_path)
    if not path.exists():
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        print(f"Error: config file must contain a YAML mapping.", file=sys.stderr)
        sys.exit(1)
    return config


def _cli_progress(step: int, total: int, role: str, backend: str, latency_ms: int) -> None:
    """Print progress to stderr."""
    seconds = latency_ms / 1000
    print(f"[{step}/{total}] {role} ({backend})... done ({seconds:.0f}s)", file=sys.stderr)


def _data_flow_prompt(backend_ids: set[str]) -> bool:
    """Prompt the user about data flow to external backends. Returns True to proceed."""
    from llm_council_mcp.backends import parse_backend_id

    external = []
    local = []
    for bid in sorted(backend_ids):
        provider, _ = parse_backend_id(bid)
        if provider == "ollama":
            local.append(f"  - {bid} (local)")
        else:
            external.append(f"  - {bid} (external API)")

    if not external:
        return True  # All local, no prompt needed.

    lines = external + local
    print(
        f"\nThis evaluation will send the artifact to {len(backend_ids)} backends:\n"
        + "\n".join(lines)
        + "\n\nProceed? [Y/n] ",
        file=sys.stderr,
        end="",
    )
    response = input().strip().lower()
    return response in ("", "y", "yes")


def cmd_evaluate(args: argparse.Namespace) -> None:
    """Evaluate an artifact using the LLM Council."""
    artifact = _read_artifact(args.artifact)

    if args.dry_run:
        prompt = build_evaluation_prompt(artifact)
        print(prompt)
        return

    config_dict = None
    backend = getattr(args, "backend", None)
    config_path = getattr(args, "config", None)

    if backend and config_path:
        print("Error: Specify --backend or --config, not both.", file=sys.stderr)
        sys.exit(1)

    if config_path:
        config_dict = _load_config(config_path)

    if not backend and not config_path:
        print(
            "Error: CLI requires a backend. Use --backend or --config.\n"
            "  llm-council evaluate my_doc.md --backend anthropic\n"
            "  llm-council evaluate my_doc.md --config council_config.yaml\n"
            "  llm-council evaluate my_doc.md --dry-run\n"
            "See --help for details.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Use the orchestrator for all backend-driven evaluations.
    from llm_council_mcp.orchestrator import CouncilOrchestrator

    orchestrator = CouncilOrchestrator(
        artifact=artifact,
        backend=backend if backend != "auto" else None,
        config=config_dict,
        progress_callback=_cli_progress,
    )

    # Validation.
    errors = orchestrator.validate()
    if errors:
        print("Error:\n" + "\n".join(f"  - {e}" for e in errors), file=sys.stderr)
        sys.exit(1)

    # Data flow confirmation (unless --yes or single/local backend).
    if not getattr(args, "yes", False):
        all_backends = orchestrator._collect_all_backend_ids()
        if len(all_backends) > 1 or any(
            not bid.startswith("ollama") for bid in all_backends
        ):
            # Only prompt if multiple backends or any external backend.
            from llm_council_mcp.backends import parse_backend_id
            external_count = sum(
                1 for bid in all_backends
                if parse_backend_id(bid)[0] != "ollama"
            )
            if external_count > 1:
                if not _data_flow_prompt(all_backends):
                    print("Aborted.", file=sys.stderr)
                    sys.exit(0)

    # Run.
    result = asyncio.run(orchestrator.run())
    print(result)


def cmd_inspect(args: argparse.Namespace) -> None:
    """Show what artifact type and personas would be selected for a given artifact."""
    artifact = _read_artifact(args.artifact)
    artifact_type = infer_artifact_type(artifact)
    personas = get_personas(artifact_type)

    config_path = getattr(args, "config", None)

    print(f"Detected artifact type: {artifact_type}\n")

    if config_path:
        config = _load_config(config_path)
        config_personas = config.get("personas", [])
        default_backend = config.get("default_backend", "anthropic/claude-sonnet-4-20250514")
        aggregation_backend = config.get("aggregation_backend", default_backend)

        print(f"Default backend: {default_backend}")
        print(f"Aggregation backend: {aggregation_backend}\n")
        print(f"Persona-backend mapping ({len(config_personas)} personas):\n")
        for i, p in enumerate(config_personas, 1):
            role = p.get("role", "?")
            backend = p.get("backend", default_backend)
            temp = p.get("temperature", "")
            temp_str = f" (temperature: {temp})" if temp else ""
            print(f"  {i}. {role} → {backend}{temp_str}")
        print()
    else:
        print(f"Reviewer personas ({len(personas)}):\n")
        for i, persona in enumerate(personas, 1):
            print(f"  {i}. {persona['role']}")
            print(f"     {persona['perspective']}\n")


def cmd_personas(args: argparse.Namespace) -> None:
    """List all available persona sets."""
    for artifact_type, personas in _PERSONAS_BY_TYPE.items():
        print(f"=== {artifact_type} ({len(personas)} personas) ===\n")
        for i, persona in enumerate(personas, 1):
            print(f"  {i}. {persona['role']}")
            print(f"     {persona['perspective']}\n")


def cmd_generate_config(args: argparse.Namespace) -> None:
    """Generate a starter YAML config for an artifact or artifact type."""
    import yaml as _yaml

    # Determine artifact type.
    if args.type:
        artifact_type = args.type
    elif args.artifact:
        artifact = _read_artifact(args.artifact)
        artifact_type = infer_artifact_type(artifact)
    else:
        artifact_type = "code"

    personas = get_personas(artifact_type)
    default_backend = args.default_backend or "anthropic/claude-sonnet-4-20250514"

    config = {
        "default_backend": default_backend,
        "aggregation_backend": default_backend,
        "personas": [],
    }

    for p in personas:
        entry = {
            "role": p["role"],
            "backend": default_backend,
            "temperature": 0.3,
        }
        config["personas"].append(entry)

    # Add comment header manually since pyyaml doesn't support comments.
    header = (
        f"# LLM Council config for artifact type: {artifact_type}\n"
        f"# Generated by: llm-council generate-config\n"
        f"#\n"
        f"# Edit the 'backend' field for each persona to assign different LLMs.\n"
        f"# Supported backends: anthropic, openai, ollama\n"
        f"# With model suffix: anthropic/claude-opus-4-20250514, openai/gpt-4o-mini, ollama/mistral\n"
        f"#\n"
        f"# Usage: llm-council evaluate my_doc.md --config this_file.yaml\n"
        f"#\n"
    )
    body = _yaml.dump(config, default_flow_style=False, sort_keys=False)
    print(header + body)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="llm-council",
        description="Evaluate artifacts using the LLM Council methodology — "
        "multi-persona review with democratic aggregation.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- evaluate ---
    eval_parser = subparsers.add_parser(
        "evaluate",
        help="Evaluate an artifact using the LLM Council",
        description=(
            "Pass a file path or '-' for stdin. Use --backend for single-backend "
            "mode or --config for per-persona mode. Use --dry-run to just print "
            "the generated prompt without calling an LLM."
        ),
    )
    eval_parser.add_argument(
        "artifact",
        help="Path to the artifact file, or '-' to read from stdin",
    )
    eval_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the evaluation prompt without calling an LLM",
    )
    eval_parser.add_argument(
        "--backend",
        help=(
            "LLM backend for all personas (e.g., 'anthropic', 'openai/gpt-4o', "
            "'ollama/llama3.2:3b')"
        ),
    )
    eval_parser.add_argument(
        "--config",
        help="Path to a YAML config file for per-persona backend assignment",
    )
    eval_parser.add_argument(
        "--model",
        help="Model override (only used with --backend, e.g., 'claude-opus-4-20250514')",
    )
    eval_parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip data flow confirmation prompt",
    )

    # --- inspect ---
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Show detected artifact type and personas without evaluating",
    )
    inspect_parser.add_argument(
        "artifact",
        help="Path to the artifact file, or '-' to read from stdin",
    )
    inspect_parser.add_argument(
        "--config",
        help="Path to a YAML config file to show persona-backend mapping",
    )

    # --- personas ---
    subparsers.add_parser(
        "personas",
        help="List all available persona sets",
    )

    # --- generate-config ---
    genconfig_parser = subparsers.add_parser(
        "generate-config",
        help="Generate a starter YAML config with all personas for an artifact type",
        description=(
            "Outputs a YAML config file to stdout with all personas for the "
            "detected (or specified) artifact type. Redirect to a file, then "
            "edit the backend assignments. Example:\n"
            "  llm-council generate-config --type code > my_config.yaml"
        ),
    )
    genconfig_parser.add_argument(
        "artifact",
        nargs="?",
        help="Path to an artifact file to auto-detect type (optional)",
    )
    genconfig_parser.add_argument(
        "--type",
        choices=["code", "design_doc", "plan", "general"],
        help="Artifact type (instead of auto-detecting from a file)",
    )
    genconfig_parser.add_argument(
        "--default-backend",
        help="Default backend for all personas (default: anthropic/claude-sonnet-4-20250514)",
    )

    args = parser.parse_args()

    # Handle --backend with --model override.
    if args.command == "evaluate" and args.backend and args.model:
        args.backend = f"{args.backend}/{args.model}"

    if args.command == "evaluate":
        cmd_evaluate(args)
    elif args.command == "inspect":
        cmd_inspect(args)
    elif args.command == "personas":
        cmd_personas(args)
    elif args.command == "generate-config":
        cmd_generate_config(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
