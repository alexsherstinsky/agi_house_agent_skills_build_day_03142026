from llm_council import CouncilMember, TestCase

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


def main():
    test_cases = [
        TestCase(question="What are the most important qualities of a good software engineer?"),
        TestCase(question="How should a team handle technical debt?"),
        TestCase(question="What makes a software architecture decision good or bad?"),
    ]

    for test in test_cases:
        print(f"\n{'#'*60}")
        print(f"Question: {test.question}")
        print('#'*60)
        for member in COUNCIL_MEMBERS:
            print(f"\n{'='*60}")
            print(f"Council Member: {member.name}")
            print('='*60)
            print(member.ask(test.question))


if __name__ == "__main__":
    main()
