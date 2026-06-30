"""Thin async wrapper around the OpenAI SDK (pointed at OpenRouter).

Uses the proper chat-completions interface with role-based messages and
function/tool calling, instead of stuffing the whole conversation into one
string. Retries and timeouts are handled by the SDK.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import AsyncIterator

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessage

from core.config import settings


def _reconstruct_message(content_parts: list[str], tool_calls: dict[int, dict]):
    """Rebuild an assistant message from streamed deltas.

    Mimics the shape the agent loop expects (``.content`` and ``.tool_calls`` with
    ``.id`` / ``.function.name`` / ``.function.arguments``) using ``SimpleNamespace``.
    """
    calls = []
    for index in sorted(tool_calls):
        slot = tool_calls[index]
        if not slot["name"]:
            continue
        calls.append(
            SimpleNamespace(
                id=slot["id"] or f"call_{index}",
                type="function",
                function=SimpleNamespace(
                    name=slot["name"], arguments=slot["arguments"] or "{}"
                ),
            )
        )
    return SimpleNamespace(
        content="".join(content_parts) or None,
        tool_calls=calls or None,
    )


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

    async def stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[tuple[str, object]]:
        """Stream one chat-completions call.

        Yields ``("token", text)`` for each content delta as it arrives, then a
        final ``("message", message)`` event carrying the fully reconstructed
        assistant message (content + any ``tool_calls``). Token usage and the
        served model are recorded on the client, mirroring :meth:`complete`.
        """
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": (
                settings.llm.temperature if temperature is None else temperature
            ),
            "max_tokens": settings.llm.max_tokens if max_tokens is None else max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        self.last_usage = None
        self.last_model = None
        content_parts: list[str] = []
        tool_calls: dict[int, dict] = {}  # index -> {id, name, arguments}

        stream = await self._client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if getattr(chunk, "model", None):
                self.last_model = chunk.model
            usage = getattr(chunk, "usage", None)
            if usage:
                self.last_usage = {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                }

            choices = getattr(chunk, "choices", None)
            if not choices:
                continue
            delta = choices[0].delta
            if delta is None:
                continue

            if delta.content:
                content_parts.append(delta.content)
                yield "token", delta.content

            for call in delta.tool_calls or []:
                slot = tool_calls.setdefault(
                    call.index, {"id": None, "name": "", "arguments": ""}
                )
                if call.id:
                    slot["id"] = call.id
                fn = getattr(call, "function", None)
                if fn and fn.name:
                    slot["name"] = fn.name
                if fn and fn.arguments:
                    slot["arguments"] += fn.arguments

        yield "message", _reconstruct_message(content_parts, tool_calls)
