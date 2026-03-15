"""
Run LLM Council evaluation on a document using local llama model.
Usage: python review_doc.py <doc_path>
"""
import pathlib
import sys
from datetime import date

from llm_council import CouncilMember

COUNCIL_MEMBERS = [
    CouncilMember(
        name="Software Engineer",
        system="You are a software engineer reviewing a design document. Focus on correctness, bugs, edge cases, and logic errors. Be specific and technical.",
    ),
    CouncilMember(
        name="Code Reviewer",
        system="You are a senior code reviewer. Focus on readability, maintainability, conventions, and clarity of the design. Point out ambiguities.",
    ),
    CouncilMember(
        name="Security Engineer",
        system="You are a security engineer. Focus on vulnerabilities, input validation, injection risks, authentication, and data exposure.",
    ),
    CouncilMember(
        name="Performance Engineer",
        system="You are a performance engineer. Focus on latency, throughput, memory usage, scalability concerns, and unnecessary work.",
    ),
    CouncilMember(
        name="QA Engineer",
        system="You are a QA engineer. Focus on testability, missing test cases, edge cases, error handling, and observability.",
    ),
]

LENSES = {
    "Software Engineer": "Correctness, bugs, edge cases, logic errors.",
    "Code Reviewer": "Readability, maintainability, conventions.",
    "Security Engineer": "Vulnerabilities, input validation, injection risks.",
    "Performance Engineer": "Performance concerns, unnecessary work, scalability.",
    "QA Engineer": "Testability, edge cases, missing test cases.",
}


def main():
    doc_path = pathlib.Path(sys.argv[1])
    doc_content = doc_path.read_text()

    question = (
        "Please review the following software design document. "
        "Provide a detailed critique based on your area of expertise. "
        "List specific issues with severity (Important/Medium/Minor) and recommendations.\n\n"
        f"{doc_content}"
    )

    print("=== Running LLM Council Evaluation (llama3.2:3b) ===\n")

    reviews = {}
    for member in COUNCIL_MEMBERS:
        print(f"  [{member.name}] reviewing...")
        reviews[member.name] = member.ask(question)
        print(f"  Done.\n")

    # Ask one member for overall score and summary
    print("  [Aggregating] computing overall score...")
    aggregator = COUNCIL_MEMBERS[0]
    all_reviews = "\n\n".join(
        f"=== {name} ===\n{review}" for name, review in reviews.items()
    )
    score_prompt = (
        "Based on these 5 expert reviews of a software design document, "
        "provide: (1) an overall quality score out of 10, (2) a one-paragraph summary "
        "of the main issues, (3) an overall readiness assessment (Ready / Needs Revision / Major Rework).\n\n"
        f"{all_reviews}"
    )
    aggregation = aggregator.ask(score_prompt)
    print("  Done.\n")

    # Build output markdown
    today = date.today().isoformat()
    doc_name = doc_path.stem
    lines = [
        f"# LLM Council Evaluation — {doc_name}\n",
        f"**Source artifact:** `{doc_path}`",
        f"**Evaluation date:** {today}",
        "**LLM backend:** llama3.2:3b (local, via Ollama)",
        "**Method:** LLM Council — 5 independent reviewers\n",
        "---\n",
    ]

    for member in COUNCIL_MEMBERS:
        lines.append(f"## Reviewer: {member.name}\n")
        lines.append(f"**Lens:** {LENSES[member.name]}\n")
        lines.append(reviews[member.name])
        lines.append("\n---\n")

    lines.append("## Aggregation\n")
    lines.append(aggregation)
    lines.append("\n")

    out = doc_path.parent / f"{doc_path.stem}.llm_council_evaluation.llama.md"
    out.write_text("\n".join(lines))
    print(f"Evaluation written to {out}")


if __name__ == "__main__":
    main()
