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
