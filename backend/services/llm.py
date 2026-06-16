import json
from collections.abc import AsyncGenerator

from google import genai
from google.genai import types

from backend.config import get_settings


def _content_from_messages(system_prompt: str, messages: list[dict[str, str]]) -> list[types.Content]:
    contents = [types.Content(role="user", parts=[types.Part(text=system_prompt)])]
    for message in messages:
        role = "model" if message["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=message["content"])]))
    return contents


class GeminiClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.gemini_model
        self.client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    async def complete(self, system_prompt: str, messages: list[dict[str, str]], max_tokens: int = 2048) -> str:
        if self.client is None:
            return "Gemini is not configured. Add GEMINI_API_KEY to enable live responses."
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=_content_from_messages(system_prompt, messages),
            config=types.GenerateContentConfig(max_output_tokens=max_tokens),
        )
        return response.text or ""

    async def stream(self, system_prompt: str, messages: list[dict[str, str]], max_tokens: int = 2048) -> AsyncGenerator[str, None]:
        if self.client is None:
            yield "Gemini is not configured. Add GEMINI_API_KEY to enable live responses."
            return
        stream = await self.client.aio.models.generate_content_stream(
            model=self.model,
            contents=_content_from_messages(system_prompt, messages),
            config=types.GenerateContentConfig(max_output_tokens=max_tokens),
        )
        async for chunk in stream:
            if chunk.text:
                yield chunk.text

    async def complete_json(self, prompt: str, content: str) -> dict:
        raw = await self.complete(prompt, [{"role": "user", "content": content}], max_tokens=2048)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.removeprefix("json").strip()
        return json.loads(cleaned)


gemini_client = GeminiClient()
