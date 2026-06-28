"""Tests for the agent loop using a scripted (fake) LLM client — no network."""

import json
from dataclasses import dataclass

import pytest

from features.llm.agent import run_agent, run_agent_events


@dataclass
class FakeFunction:
    name: str
    arguments: str


@dataclass
class FakeToolCall:
    id: str
    function: FakeFunction


@dataclass
class FakeMessage:
    content: str | None = None
    tool_calls: list | None = None


class ScriptedClient:
    """Returns pre-scripted assistant messages and records each call."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    async def complete(self, messages, tools=None, **kwargs):
        self.calls.append({"messages": list(messages), "tools": tools})
        return self._responses.pop(0)


class HistMsg:
    def __init__(self, sender, content):
        self.sender = sender
        self.content = content


HISTORY = [HistMsg("user", "Посчитай маржу: выручка 100, себестоимость 60")]


@pytest.mark.asyncio
async def test_direct_answer_without_tools():
    client = ScriptedClient([FakeMessage(content="Здравствуйте!")])
    result = await run_agent(HISTORY, client=client)

    assert result.content == "Здравствуйте!"
    assert result.steps == []
    # Tools are offered to the model on the first call.
    assert client.calls[0]["tools"]


@pytest.mark.asyncio
async def test_single_tool_call_then_final_answer():
    tool_call = FakeToolCall(
        id="c1",
        function=FakeFunction(
            name="financial_calculator",
            arguments='{"operation": "margin", "revenue": 100, "cost": 60}',
        ),
    )
    client = ScriptedClient(
        [
            FakeMessage(tool_calls=[tool_call]),
            FakeMessage(content="Маржа составляет 40%."),
        ]
    )

    result = await run_agent(HISTORY, client=client)

    assert result.content == "Маржа составляет 40%."
    assert len(result.steps) == 1
    step = result.steps[0]
    assert step.tool == "financial_calculator"
    assert json.loads(step.result)["margin_percent"] == 40.0

    # The second call must include the tool result as a tool-role message.
    second_call_messages = client.calls[1]["messages"]
    assert any(m.get("role") == "tool" for m in second_call_messages)


@pytest.mark.asyncio
async def test_step_budget_exhaustion_forces_final_answer():
    looping_tool_call = FakeToolCall(
        id="loop",
        function=FakeFunction(name="get_current_datetime", arguments="{}"),
    )
    client = ScriptedClient(
        [
            FakeMessage(tool_calls=[looping_tool_call]),
            FakeMessage(tool_calls=[looping_tool_call]),
            FakeMessage(content="Финальный ответ."),  # forced final, no tools
        ]
    )

    result = await run_agent(HISTORY, client=client, max_steps=2)

    assert result.content == "Финальный ответ."
    assert len(result.steps) == 2
    # The forced final call must drop tools.
    assert client.calls[-1]["tools"] is None


@pytest.mark.asyncio
async def test_run_agent_events_emits_step_then_final():
    tool_call = FakeToolCall(
        id="c1",
        function=FakeFunction(name="get_current_datetime", arguments="{}"),
    )
    client = ScriptedClient(
        [FakeMessage(tool_calls=[tool_call]), FakeMessage(content="Готово.")]
    )

    kinds = [kind async for kind, _ in run_agent_events(HISTORY, client=client)]
    assert kinds == ["step", "final"]
