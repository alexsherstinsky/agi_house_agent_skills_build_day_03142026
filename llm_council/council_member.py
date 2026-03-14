import re

import ollama


class CouncilMember:
    def __init__(self, name: str, system: str, model: str = "llama3.2:3b"):
        self.name = name
        self.system = system
        self.model = model

    def ask(self, question: str) -> str:
        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system},
                {"role": "user", "content": question},
            ],
        )
        return response["message"]["content"]

    def judge(self, responses: list[dict]) -> int:
        responses_text = "\n\n".join(
            f"Q: {r['question']}\nA: {r['response']}" for r in responses
        )
        prompt = (
            "You are evaluating the following responses to software engineering questions.\n\n"
            f"{responses_text}\n\n"
            "Rate the overall quality of these responses on a scale of 0 to 100 "
            "(0 = terrible, 100 = excellent). "
            "Respond with ONLY a single integer."
        )
        raw = self.ask(prompt)
        match = re.search(r'\b(\d{1,3})\b', raw)
        return int(match.group(1)) if match else 50
