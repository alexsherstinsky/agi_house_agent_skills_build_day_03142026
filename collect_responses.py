import argparse
import json
import pathlib
from datetime import datetime
from typing import Optional

try:
    from dotenv import load_dotenv
    _env_path = pathlib.Path(__file__).resolve().parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass

from llm_council import CouncilMember, CouncilGroup, TestCase

# Dev: all Ollama (save tokens)
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

# Big models: different free Ollama models per member (run: ollama pull <model>)
COUNCIL_MEMBERS_BIG = [
    CouncilMember(
        name="Senior Engineer",
        system="You are a pragmatic senior software engineer with 20 years of experience shipping production systems. You value reliability, simplicity, and clear communication above all.",
        provider="ollama",
        model="llama3.2:3b",
    ),
    CouncilMember(
        name="Engineering Manager",
        system="You are an engineering manager focused on team performance and career growth. You think about qualities in terms of collaboration, ownership, and impact on the team.",
        provider="ollama",
        model="gemma3",
    ),
    CouncilMember(
        name="Computer Science Professor",
        system="You are a CS professor who values theoretical foundations, intellectual curiosity, and rigorous problem-solving. You tend to reference first principles and academic thinking.",
        provider="ollama",
        model="gemini-3-flash-preview",
    ),
]


def main(
    council_members: Optional[list[CouncilMember]] = None,
    output_path: Optional[pathlib.Path] = None,
):
    members = council_members or COUNCIL_MEMBERS
    test_cases = [
        TestCase(question="What are the most important qualities of a good software engineer?"),
        TestCase(question="How should a team handle technical debt?"),
        TestCase(question="What makes a software architecture decision good or bad?"),
    ]

    # Collect responses
    results = []
    for test in test_cases:
        for member in members:
            if isinstance(member, CouncilGroup):
                names = ", ".join(m.name for m in member.members)
                print(f"  [{names}] answering: {test.question}")
            else:
                print(f"  {member.name} answering: {test.question}")
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

    if output_path is None:
        output_path = pathlib.Path(__file__).parent / "tmp" / "llm_council_results.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))
    print(f"Results written to {output_path}")

    json_data = [
        {"question": r["test"].question, "member_name": r["member"].name, "response": r["response"]}
        for r in results
    ]
    json_path = output_path.with_suffix(".json")
    json_path.write_text(json.dumps(json_data, indent=2))
    print(f"Results JSON written to {json_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect LLM Council responses from each member.",
    )
    parser.add_argument(
        "--big-models",
        action="store_true",
        help="Use different Ollama models per member (llama3.2:3b, mistral, phi3)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    members = COUNCIL_MEMBERS_BIG if args.big_models else COUNCIL_MEMBERS
    mode = "big-models" if args.big_models else "default"
    if args.big_models:
        print("Using different models for different council members\n")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_dir = pathlib.Path(__file__).parent / "tmp"
    output_path = tmp_dir / f"llm_council_results_{mode}_{timestamp}.md"
    main(council_members=members, output_path=output_path)
