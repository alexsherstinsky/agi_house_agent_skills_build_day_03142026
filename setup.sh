#!/usr/bin/env bash
set -euo pipefail

# Install Ollama via Homebrew
if ! command -v ollama &>/dev/null; then
    echo "Installing Ollama..."
    brew install ollama
else
    echo "Ollama already installed: $(ollama --version)"
fi
