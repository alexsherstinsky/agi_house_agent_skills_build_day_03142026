"""Council member: Ollama (default) or OpenAI / Claude / Gemini when provider/model set."""

from __future__ import annotations

import re

from llm_council.config import Provider, resolve_provider_and_model


def _chat_ollama(model: str, system: str, user: str) -> str:
    import ollama

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response["message"]["content"]


def _chat_openai(model: str, system: str, user: str) -> str:
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""


def _chat_anthropic(model: str, system: str, user: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def _chat_gemini(model: str, system: str, user: str) -> str:
    import google.generativeai as genai

    genai.configure()
    m = genai.GenerativeModel(model, system_instruction=system)
    response = m.generate_content(user)
    return response.text or ""


def _chat(provider: Provider, model: str, system: str, user: str) -> str:
    if provider == "ollama":
        return _chat_ollama(model, system, user)
    if provider == "openai":
        return _chat_openai(model, system, user)
    if provider == "anthropic":
        return _chat_anthropic(model, system, user)
    if provider == "gemini":
        return _chat_gemini(model, system, user)
    raise ValueError(f"Unknown provider: {provider}")


class CouncilMember:
    """A council member that answers and judges using an LLM.

    Default: Ollama with llama3.2:3b. Pass provider/model to use OpenAI, Claude, or Gemini.
    """

    def __init__(
        self,
        name: str,
        system: str,
        model: str | None = None,
        *,
        provider: Provider | None = None,
    ):
        self.name = name
        self.system = system
        self._provider, self._model = resolve_provider_and_model(provider, model)

    @property
    def provider(self) -> Provider:
        return self._provider

    @property
    def model(self) -> str:
        return self._model

    def ask(self, question: str) -> str:
        return _chat(self._provider, self._model, self.system, question)

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
        match = re.search(r"\b(\d{1,3})\b", raw)
        return int(match.group(1)) if match else 50
