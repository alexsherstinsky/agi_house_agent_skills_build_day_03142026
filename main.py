import ollama

MODEL = "llama3.2:3b"
QUESTION = "What are the most important qualities of a good software engineer?"

PROMPTS = [
    QUESTION,
    f"Answer in 2-3 sentences: {QUESTION}",
    f"Think step by step, then answer: {QUESTION}",
]

for i, prompt in enumerate(PROMPTS, 1):
    print(f"\n{'='*60}")
    print(f"Prompt {i}: {prompt}")
    print('='*60)
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    print(response["message"]["content"])
