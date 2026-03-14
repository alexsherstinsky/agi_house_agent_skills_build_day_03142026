#!/usr/bin/env bash
set -euo pipefail

# Install Ollama via Homebrew
if ! command -v ollama &>/dev/null; then
    echo "Installing Ollama..."
    brew install ollama
else
    echo "Ollama already installed: $(ollama --version)"
fi

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Install Python dependencies
echo "Installing Python dependencies..."
.venv/bin/pip install --quiet -e .
echo "Done. Activate with: source .venv/bin/activate"
