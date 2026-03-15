import pathlib

from llm_council import CouncilMember, CouncilGroup, TestCase

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
    CouncilGroup(
        members=[
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
        ],
    ),
]


def main():
    test_cases = [
        TestCase(question="What are the most important qualities of a good software engineer?"),
        TestCase(question="How should a team handle technical debt?"),
        TestCase(question="What makes a software architecture decision good or bad?"),
    ]

    # Collect responses
    results = []
    for test in test_cases:
        for member in COUNCIL_MEMBERS:
            response = member.ask(test.question)
            results.append({"test": test, "member": member, "response": response})

    # Write markdown
    lines = ["# LLM Council Results\n"]
    current_question = None
    for r in results:
        if r["test"].question != current_question:
            current_question = r["test"].question
            lines.append(f"\n## {current_question}\n")
        lines.append(f"### {r['member'].name}\n")
        lines.append(f"{r['response']}\n")

    out = pathlib.Path(__file__).parent / "tmp" / "llm_council_results.md"
    out.write_text("\n".join(lines))
    print(f"Results written to {out}")


if __name__ == "__main__":
    main()
