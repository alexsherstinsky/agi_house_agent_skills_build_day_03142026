#!/usr/bin/env bash
set -euo pipefail

MODEL="llama3.2:3b"

# 1. Check ollama is installed
if ! command -v ollama &>/dev/null; then
    echo "Error: ollama is not installed. Install it from https://ollama.com" >&2
    exit 1
fi

# 2. Pull model if not present
if ! ollama list 2>/dev/null | grep -q "^${MODEL}"; then
    echo "Pulling ${MODEL} model..."
    ollama pull "${MODEL}"
fi

# 3. Run — pass any arguments straight through
ollama run "${MODEL}" "$@"
