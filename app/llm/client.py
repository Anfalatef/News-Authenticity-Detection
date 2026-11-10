from __future__ import annotations

from typing import Any

from openai import OpenAI


class LLMClient:
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing. Put it in .env and ensure load_dotenv() runs.")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def chat(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
        )
        text = resp.choices[0].message.content or ""
        return {"model": self.model, "text": text.strip()}
