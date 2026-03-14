import statistics

import ollama

from .council_member import CouncilMember


class CouncilGroup:
    def __init__(
        self,
        members: list[CouncilMember],
        model: str = "llama3.2:3b",
        detailed: bool = False,
    ):
        self.members = members
        self.model = model
        self.detailed = detailed

    def ask(self, question: str) -> str | dict:
        """Ask every member independently, then synthesize a unified response.

        Returns just the unified string by default, or a full dict with
        'individual' and 'unified' when detailed=True.
        """
        individual = []
        for member in self.members:
            response = member.ask(question)
            individual.append({
                "name": member.name,
                "response": response,
            })

        unified = self._synthesize(question, individual)
        if self.detailed:
            return {"individual": individual, "unified": unified}
        return unified

    def _synthesize(self, question: str, individual: list[dict]) -> str:
        perspectives = "\n\n".join(
            f"### {r['name']}\n{r['response']}" for r in individual
        )
        prompt = (
            f"Original question: {question}\n\n"
            f"The following {len(individual)} independent experts each answered "
            "this question from their own perspective:\n\n"
            f"{perspectives}\n\n"
            "Synthesize these into a single unified response that:\n"
            "1. Captures the key points all experts agree on\n"
            "2. Includes important unique insights from individual experts\n"
            "3. Notes any meaningful disagreements\n"
            "4. Is concise and actionable\n\n"
            "Write the unified response directly — do not reference the experts by name."
        )
        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a skilled synthesizer. Your job is to combine "
                        "multiple expert perspectives into a single coherent, "
                        "balanced response."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response["message"]["content"]

    def judge(self, responses: list[dict]) -> int | dict:
        """Each member judges the responses independently; return the mean score.

        Returns just the mean int by default, or a full dict with per-member
        'scores', 'mean', and 'stdev' when detailed=True.
        """
        scores = []
        for member in self.members:
            score = member.judge(responses)
            scores.append({"name": member.name, "score": score})

        values = [s["score"] for s in scores]
        mean = round(statistics.mean(values))
        if self.detailed:
            return {
                "scores": scores,
                "mean": mean,
                "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
            }
        return mean
