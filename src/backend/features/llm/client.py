"""Thin async wrapper around the OpenAI SDK (pointed at OpenRouter).

Uses the proper chat-completions interface with role-based messages and
function/tool calling, instead of stuffing the whole conversation into one
string. Retries and timeouts are handled by the SDK.
"""

from __future__ import annotations

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessage

from core.config import settings


class LLMClient:
    def __init__(self, model: str | None = None):
        self.model = model or settings.llm.default_model
        self.last_usage: dict | None = None
        self.last_model: str | None = None  # model the API actually served
        self._client = AsyncOpenAI(
            api_key=settings.llm.api_key,
            base_url=settings.llm.api_base,
            timeout=settings.llm.request_timeout,
            max_retries=3,
        )

    async def complete(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatCompletionMessage:
        """One chat-completions call. Returns the assistant message, which may
        contain ``tool_calls`` instead of (or alongside) text content."""
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": (
                settings.llm.temperature if temperature is None else temperature
            ),
            "max_tokens": settings.llm.max_tokens if max_tokens is None else max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self._client.chat.completions.create(**kwargs)
        self.last_model = getattr(response, "model", None)
        usage = getattr(response, "usage", None)
        self.last_usage = (
            {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
            }
            if usage
            else None
        )
        return response.choices[0].message
