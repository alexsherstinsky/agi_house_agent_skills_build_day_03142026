#!/usr/bin/env python3
"""LLM Council MCP Server.

A standalone, domain-agnostic MCP tool that evaluates any artifact using
the LLM Council methodology (Zhao et al., 2024) — multi-persona review
with democratic aggregation.

Usage:
    python -m llm_council_mcp.server
"""

from __future__ import annotations

import asyncio
import json

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
                "reviewer personas."
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


async def main() -> None:
    """Run the MCP server via stdio."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
