from llm_council import CouncilMember

QUESTION = "What are the most important qualities of a good software engineer?"

COUNCIL_MEMBERS = [
    CouncilMember(
        name="Senior Engineer",
        system="You are a pragmatic senior software engineer with 20 years of experience shipping production systems. You value reliability, simplicity, and clear communication above all.",
    ),
    CouncilMember(
        name="Engineering Manager",
        system="You are an engineering manager focused on team performance and career growth. You think about qualities in terms of collaboration, ownership, and impact on the team.",
    ),
    CouncilMember(
        name="Computer Science Professor",
        system="You are a CS professor who values theoretical foundations, intellectual curiosity, and rigorous problem-solving. You tend to reference first principles and academic thinking.",
    ),
]

for member in COUNCIL_MEMBERS:
    print(f"\n{'='*60}")
    print(f"Council Member: {member.name}")
    print('='*60)
    print(member.ask(QUESTION))
