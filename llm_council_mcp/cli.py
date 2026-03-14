#!/usr/bin/env python3
"""LLM Council CLI.

Evaluate any artifact from the command line using the LLM Council methodology.

Usage:
    # Evaluate a file
    llm-council evaluate my_code.py

    # Pipe text in
    cat design_doc.md | llm-council evaluate -

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
import json
import sys
from pathlib import Path

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


def cmd_evaluate(args: argparse.Namespace) -> None:
    """Evaluate an artifact using the LLM Council."""
    artifact = _read_artifact(args.artifact)
    artifact_type = infer_artifact_type(artifact)
    personas = get_personas(artifact_type)

    if args.dry_run:
        prompt = build_evaluation_prompt(artifact)
        print(prompt)
        return

    # Call an LLM to perform the evaluation.
    prompt = build_evaluation_prompt(artifact)

    if args.backend == "anthropic":
        _evaluate_with_anthropic(prompt, model=args.model)
    elif args.backend == "ollama":
        _evaluate_with_ollama(prompt, model=args.model)
    else:
        # Auto-detect: try anthropic first, fall back to ollama.
        try:
            import anthropic  # noqa: F401
            _evaluate_with_anthropic(prompt, model=args.model)
        except ImportError:
            try:
                import ollama  # noqa: F401
                _evaluate_with_ollama(prompt, model=args.model)
            except ImportError:
                print(
                    "Error: no LLM backend available.\n"
                    "Install one of:\n"
                    "  uv pip install anthropic    # for Claude API\n"
                    "  uv pip install ollama       # for local Ollama\n"
                    "\nOr use --dry-run to just print the evaluation prompt.",
                    file=sys.stderr,
                )
                sys.exit(1)


def _evaluate_with_anthropic(prompt: str, model: str | None = None) -> None:
    """Run the evaluation using the Anthropic (Claude) API."""
    try:
        import anthropic
    except ImportError:
        print(
            "Error: 'anthropic' package not installed.\n"
            "Run: uv pip install anthropic",
            file=sys.stderr,
        )
        sys.exit(1)

    model = model or "claude-sonnet-4-20250514"
    client = anthropic.Anthropic()

    print(f"Running LLM Council evaluation via Claude ({model})...\n", file=sys.stderr)

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    print(response.content[0].text)


def _evaluate_with_ollama(prompt: str, model: str | None = None) -> None:
    """Run the evaluation using a local Ollama model."""
    try:
        import ollama
    except ImportError:
        print(
            "Error: 'ollama' package not installed.\n"
            "Run: uv pip install ollama",
            file=sys.stderr,
        )
        sys.exit(1)

    model = model or "llama3.2:3b"

    print(f"Running LLM Council evaluation via Ollama ({model})...\n", file=sys.stderr)

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    print(response["message"]["content"])


def cmd_inspect(args: argparse.Namespace) -> None:
    """Show what artifact type and personas would be selected for a given artifact."""
    artifact = _read_artifact(args.artifact)
    artifact_type = infer_artifact_type(artifact)
    personas = get_personas(artifact_type)

    print(f"Detected artifact type: {artifact_type}\n")
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
            "Pass a file path or '-' for stdin. By default, calls an LLM to "
            "perform the full Council evaluation. Use --dry-run to just print "
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
        choices=["anthropic", "ollama", "auto"],
        default="auto",
        help="LLM backend to use (default: auto-detect)",
    )
    eval_parser.add_argument(
        "--model",
        help="Model name to use (default: claude-sonnet-4-20250514 for anthropic, llama3.2:3b for ollama)",
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

    # --- personas ---
    subparsers.add_parser(
        "personas",
        help="List all available persona sets",
    )

    args = parser.parse_args()

    if args.command == "evaluate":
        cmd_evaluate(args)
    elif args.command == "inspect":
        cmd_inspect(args)
    elif args.command == "personas":
        cmd_personas(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
