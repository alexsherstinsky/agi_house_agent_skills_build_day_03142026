# AGI House Agent Skills Build Day

## Setup

Install Ollama via Homebrew:

```bash
./setup.sh
```

## Running the model

Run `llama3.2:3b` locally (pulls the model automatically on first run):

```bash
# Interactive chat
./scripts/run_llama.sh

# One-shot prompt
./scripts/run_llama.sh "What is 2+2?"
```
