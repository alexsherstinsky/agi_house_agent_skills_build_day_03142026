import ollama

MODEL = "llama3.2:3b"
QUESTION = "What are the most important qualities of a good software engineer?"

COUNCIL_MEMBERS = [
    {
        "name": "Senior Engineer",
        "system": "You are a pragmatic senior software engineer with 20 years of experience shipping production systems. You value reliability, simplicity, and clear communication above all.",
    },
    {
        "name": "Engineering Manager",
        "system": "You are an engineering manager focused on team performance and career growth. You think about qualities in terms of collaboration, ownership, and impact on the team.",
    },
    {
        "name": "Computer Science Professor",
        "system": "You are a CS professor who values theoretical foundations, intellectual curiosity, and rigorous problem-solving. You tend to reference first principles and academic thinking.",
    },
]

for member in COUNCIL_MEMBERS:
    print(f"\n{'='*60}")
    print(f"Council Member: {member['name']}")
    print('='*60)
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": member["system"]},
            {"role": "user", "content": QUESTION},
        ],
    )
    print(response["message"]["content"])
