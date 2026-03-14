import json
import pathlib
import statistics

from llm_council import CouncilMember

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


def parse_results(path: pathlib.Path) -> list[dict]:
    results = []
    question = None
    member_name = None
    response_lines = []

    for line in path.read_text().splitlines():
        if line.startswith("## "):
            question = line[3:].strip()
        elif line.startswith("### "):
            if member_name and response_lines:
                results.append({
                    "question": question,
                    "member_name": member_name,
                    "response": "\n".join(response_lines).strip(),
                })
            member_name = line[4:].strip()
            response_lines = []
        elif member_name:
            response_lines.append(line)

    if member_name and response_lines:
        results.append({
            "question": question,
            "member_name": member_name,
            "response": "\n".join(response_lines).strip(),
        })

    return results


def main():
    results_path = pathlib.Path(__file__).parent / "tmp" / "llm_council_results.md"
    responses = parse_results(results_path)

    # Group responses by member name
    by_member: dict[str, list[dict]] = {}
    for r in responses:
        by_member.setdefault(r["member_name"], []).append(
            {"question": r["question"], "response": r["response"]}
        )

    judged_names = [m.name for m in COUNCIL_MEMBERS]

    # Collect 9 scores: (judge, judged) pairs
    scores: dict[tuple[str, str], int] = {}
    for judge in COUNCIL_MEMBERS:
        for judged_name in judged_names:
            print(f"  {judge.name} judging {judged_name}...")
            score = judge.judge(by_member[judged_name])
            scores[(judge.name, judged_name)] = score
            print(f"    → {score}")

    # Compute mean and stdev per judged member
    stats: dict[str, dict] = {}
    for judged_name in judged_names:
        judge_scores = [scores[(j.name, judged_name)] for j in COUNCIL_MEMBERS]
        stats[judged_name] = {
            "mean": statistics.mean(judge_scores),
            "stdev": statistics.stdev(judge_scores) if len(judge_scores) > 1 else 0.0,
        }

    # Build markdown table
    header = "| Judge | " + " | ".join(judged_names) + " |"
    separator = "|---" * (len(judged_names) + 1) + "|"

    rows = []
    for judge in COUNCIL_MEMBERS:
        cells = [str(scores[(judge.name, jd)]) for jd in judged_names]
        rows.append(f"| {judge.name} | " + " | ".join(cells) + " |")

    mean_cells = [f"{stats[jd]['mean']:.1f}" for jd in judged_names]
    stdev_cells = [f"{stats[jd]['stdev']:.1f}" for jd in judged_names]
    rows.append("| **Mean** | " + " | ".join(mean_cells) + " |")
    rows.append("| **Std Dev** | " + " | ".join(stdev_cells) + " |")

    lines = [
        "# LLM Council Judgments\n",
        "## Scores\n",
        "_Rows = judge, Columns = judged member_\n",
        header,
        separator,
        *rows,
    ]

    out = pathlib.Path(__file__).parent / "tmp" / "llm_council_judgments.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"\nJudgments written to {out}")

    json_data = {
        "members": judged_names,
        "scores": {j.name: {jd: scores[(j.name, jd)] for jd in judged_names} for j in COUNCIL_MEMBERS},
        "stats": stats,
    }
    json_out = pathlib.Path(__file__).parent / "tmp" / "llm_council_judgments.json"
    json_out.write_text(json.dumps(json_data, indent=2))
    print(f"Judgments JSON written to {json_out}")


if __name__ == "__main__":
    main()
