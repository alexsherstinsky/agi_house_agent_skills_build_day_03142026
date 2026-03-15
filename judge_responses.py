import argparse
import json
import pathlib
import statistics
from datetime import datetime
from typing import Optional

try:
    from dotenv import load_dotenv
    _env_path = pathlib.Path(__file__).resolve().parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass

from llm_council import CouncilMember

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


def _latest_results_path(tmp_dir: pathlib.Path) -> pathlib.Path:
    """Path to the most recent llm_council_results_*.json in tmp."""
    pattern = list(tmp_dir.glob("llm_council_results_*.json"))
    if not pattern:
        return tmp_dir / "llm_council_results.json"
    return max(pattern, key=lambda p: p.stat().st_mtime)


def main(
    council_members: Optional[list[CouncilMember]] = None,
    results_path: Optional[pathlib.Path] = None,
    output_path: Optional[pathlib.Path] = None,
):
    members = council_members or COUNCIL_MEMBERS
    tmp_dir = pathlib.Path(__file__).parent / "tmp"
    if results_path is None:
        results_path = _latest_results_path(tmp_dir)
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}. Run collect_responses.py first.")
    responses = json.loads(results_path.read_text())

    # Group responses by member name
    by_member: dict[str, list[dict]] = {}
    for r in responses:
        by_member.setdefault(r["member_name"], []).append(
            {"question": r["question"], "response": r["response"]}
        )

    # judged_names = [m.name for m in members]
    judged_names = list(by_member.keys())

    # Collect 9 scores: (judge, judged) pairs
    scores: dict[tuple[str, str], int] = {}
    for judge in members:
        for judged_name in judged_names:
            print(f"  {judge.name} judging {judged_name}...")
            score = judge.judge(by_member[judged_name])
            scores[(judge.name, judged_name)] = score
            print(f"    → {score}")

    # Compute mean and stdev per judged member
    stats: dict[str, dict] = {}
    for judged_name in judged_names:
        judge_scores = [scores[(j.name, judged_name)] for j in members]
        stats[judged_name] = {
            "mean": statistics.mean(judge_scores),
            "stdev": statistics.stdev(judge_scores) if len(judge_scores) > 1 else 0.0,
        }

    # Build markdown table
    header = "| Judge | " + " | ".join(judged_names) + " |"
    separator = "|---" * (len(judged_names) + 1) + "|"

    rows = []
    for judge in members:
        cells = [str(scores[(judge.name, jd)]) for jd in judged_names]
        rows.append(f"| {judge.name} | " + " | ".join(cells) + " |")

    mean_cells = [f"{stats[jd]['mean']:.1f}" for jd in judged_names]
    stdev_cells = [f"{stats[jd]['stdev']:.1f}" for jd in judged_names]
    rows.append(f"| **Mean** | " + " | ".join(mean_cells) + " |")
    rows.append(f"| **Std Dev** | " + " | ".join(stdev_cells) + " |")

    lines = [
        "# LLM Council Judgments\n",
        "## Scores\n",
        "_Rows = judge, Columns = judged member_\n",
        header,
        separator,
        *rows,
    ]

    if output_path is None:
        output_path = pathlib.Path(__file__).parent / "tmp" / "llm_council_judgments.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n")
    print(f"\nJudgments written to {output_path}")

    json_data = {
        "members": judged_names,
        "scores": {j.name: {jd: scores[(j.name, jd)] for jd in judged_names} for j in members},
        "stats": stats,
    }
    json_out = output_path.with_suffix(".json")
    json_out.write_text(json.dumps(json_data, indent=2))
    print(f"Judgments JSON written to {json_out}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Judge LLM Council responses and write scores.",
    )
    parser.add_argument(
        "--big-models",
        action="store_true",
        help="Use different Ollama models per member (llama3.2:3b, mistral, phi3)",
    )
    parser.add_argument(
        "--input-file",
        type=pathlib.Path,
        default=None,
        help="Results JSON file to judge (default: most recent llm_council_results_*.json in tmp/)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    members = COUNCIL_MEMBERS_BIG if args.big_models else COUNCIL_MEMBERS
    mode = "big-models" if args.big_models else "default"
    if args.big_models:
        print("Using different models for different council members\n")
    tmp_dir = pathlib.Path(__file__).parent / "tmp"
    if args.input_file is not None:
        results_path = args.input_file.resolve()
    else:
        results_path = _latest_results_path(tmp_dir)
    if not results_path.exists():
        raise SystemExit(f"Results file not found: {results_path}. Run collect_responses.py first.")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = tmp_dir / f"llm_council_judgments_{mode}_{timestamp}.md"
    main(council_members=members, results_path=results_path, output_path=output_path)
