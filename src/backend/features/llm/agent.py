"""The agent loop: reason -> call tools -> observe -> repeat -> answer.

``run_agent_events`` is the streaming core that yields steps as they happen;
``run_agent`` is a convenience wrapper that collects the final result and emits a
trace. An optional :class:`AgentTrace` collects observability data along the way.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from time import perf_counter
from typing import AsyncIterator

from core.config import settings
from features.llm.client import LLMClient
from features.llm.context_builder import build_messages
from features.llm.tools import execute_tool, get_openai_tools
from features.llm.tracing import AgentTrace, log_trace


@dataclass
class AgentStep:
    tool: str
    arguments: dict
    result: str


@dataclass
class AgentResult:
    content: str
    steps: list[AgentStep] = field(default_factory=list)
    trace: AgentTrace | None = None


def _assistant_entry(message) -> dict:
    return {
        "role": "assistant",
        "content": message.content or "",
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in message.tool_calls
        ],
    }


async def run_agent_events(
    history,
    *,
    client: LLMClient | None = None,
    max_steps: int | None = None,
    trace: AgentTrace | None = None,
    knowledge: list[str] | None = None,
) -> AsyncIterator[tuple[str, object]]:
    """Drive the agent, yielding ``("step", AgentStep)`` events as tools run and a
    final ``("final", content)`` event with the answer text."""
    client = client or LLMClient()
    max_steps = max_steps or settings.llm.max_agent_steps
    messages = build_messages(history, knowledge=knowledge)
    tools = get_openai_tools()

    for _ in range(max_steps):
        started = perf_counter()
        message = await client.complete(messages, tools=tools)
        if trace is not None:
            trace.record_llm_call(
                (perf_counter() - started) * 1000,
                getattr(client, "last_usage", None),
                resolved_model=getattr(client, "last_model", None),
            )

        tool_calls = getattr(message, "tool_calls", None)
        if not tool_calls:
            yield "final", (message.content or "")
            return

        messages.append(_assistant_entry(message))
        for call in tool_calls:
            try:
                arguments = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}

            tool_started = perf_counter()
            result = execute_tool(call.function.name, arguments)
            if trace is not None:
                trace.record_tool(
                    call.function.name, (perf_counter() - tool_started) * 1000
                )

            yield "step", AgentStep(call.function.name, arguments, result)
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": result}
            )

    # Step budget exhausted — force a final answer without tools.
    started = perf_counter()
    final = await client.complete(messages, tools=None)
    if trace is not None:
        trace.record_llm_call(
            (perf_counter() - started) * 1000,
            getattr(client, "last_usage", None),
            resolved_model=getattr(client, "last_model", None),
        )
        trace.finish_reason = "max_steps"
    yield "final", (final.content or "")


async def run_agent(
    history,
    *,
    client: LLMClient | None = None,
    max_steps: int | None = None,
    knowledge: list[str] | None = None,
) -> AgentResult:
    client = client or LLMClient()
    trace = AgentTrace.new(model=getattr(client, "model", "unknown"))

    steps: list[AgentStep] = []
    content = ""
    async for kind, payload in run_agent_events(
        history, client=client, max_steps=max_steps, trace=trace, knowledge=knowledge
    ):
        if kind == "step":
            steps.append(payload)  # type: ignore[arg-type]
        else:
            content = payload  # type: ignore[assignment]

    trace.finish()
    log_trace(trace)
    return AgentResult(content=content, steps=steps, trace=trace)
