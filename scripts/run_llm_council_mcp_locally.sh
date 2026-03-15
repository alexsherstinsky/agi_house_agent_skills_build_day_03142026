#!/usr/bin/env bash
set -euo pipefail

if [ ! -d ".venv" ]; then
    echo "No .venv found. Run ./setup.sh first." >&2
    exit 1
fi

echo "Starting LLM Council MCP server (stdio transport)..."
echo "Listening on stdin for JSON-RPC messages. Ctrl+C to stop."
.venv/bin/python3 -m llm_council_mcp.server
