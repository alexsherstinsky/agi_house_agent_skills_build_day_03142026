#!/usr/bin/env python3
"""LLM Council MCP Server.

A standalone, domain-agnostic MCP tool that evaluates any artifact using
the LLM Council methodology (Zhao et al., 2024) — multi-persona review
with democratic aggregation.

Supports three modes:
- Host mode (default): returns prompt for the host LLM to execute
- Single-backend mode: server calls one API for all personas
- Per-persona mode: server orchestrates calls to different backends per persona

Usage:
    python -m llm_council_mcp.server
"""

from __future__ import annotations

import asyncio

from mcp.server import Server
from mcp.types import TextContent, Tool

from llm_council_mcp.council import build_evaluation_prompt, infer_artifact_type


app = Server("llm-council")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="llm_council_evaluate",
            description=(
                "Evaluate an artifact (code, design doc, plan, or any text) "
                "using the LLM Council methodology — multi-persona independent "
                "review with democratic aggregation of findings. The system "
                "automatically infers artifact type and selects appropriate "
                "reviewer personas. Supports three modes: host (default, omit "
                "backend/config), single-backend (pass 'backend'), or "
                "per-persona (pass 'config')."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "artifact": {
                        "type": "string",
                        "description": (
                            "The artifact to evaluate. Can be source code, "
                            "a design document, a project plan, or any text."
                        ),
                    },
                    "backend": {
                        "type": "string",
                        "description": (
                            "LLM backend for all personas (e.g., 'anthropic', "
                            "'openai/gpt-4o', 'ollama'). Omit for host mode."
                        ),
                    },
                    "config": {
                        "type": "object",
                        "description": (
                            "Advanced: per-persona backend configuration. "
                            "Supports default_backend, aggregation_backend, "
                            "and a personas array with per-persona backend, "
                            "temperature, and max_tokens overrides."
                        ),
                        "properties": {
                            "default_backend": {"type": "string"},
                            "aggregation_backend": {"type": "string"},
                            "personas": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "role": {"type": "string"},
                                        "perspective": {"type": "string"},
                                        "backend": {"type": "string"},
                                        "temperature": {"type": "number"},
                                        "max_tokens": {"type": "integer"},
                                    },
                                    "required": ["role"],
                                },
                            },
                        },
                    },
                },
                "required": ["artifact"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name != "llm_council_evaluate":
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    artifact: str = arguments.get("artifact", "")
    if not artifact.strip():
        return [
            TextContent(
                type="text",
                text="Error: artifact is empty. Provide the text to evaluate.",
            )
        ]

    backend: str | None = arguments.get("backend")
    config: dict | None = arguments.get("config")

    # Mode resolution.
    if backend and config:
        return [
            TextContent(
                type="text",
                text="Error: Specify 'backend' or 'config', not both.",
            )
        ]

    if not backend and not config:
        # Host mode — return prompt for host LLM to execute.
        prompt = build_evaluation_prompt(artifact)
        artifact_type = infer_artifact_type(artifact)
        return [
            TextContent(
                type="text",
                text=(
                    f"Council evaluation requested for artifact "
                    f"(detected type: {artifact_type}).\n\n"
                    f"Follow the instructions below to perform the evaluation:\n\n"
                    f"{prompt}"
                ),
            )
        ]

    # Single-backend or per-persona mode — use orchestrator.
    from llm_council_mcp.orchestrator import CouncilOrchestrator

    orchestrator = CouncilOrchestrator(
        artifact=artifact,
        backend=backend,
        config=config,
    )

    result = await orchestrator.run()

    return [TextContent(type="text", text=result)]


async def main() -> None:
    """Run the MCP server via stdio."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
