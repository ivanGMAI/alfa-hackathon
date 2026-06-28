"""Tests for agent tracing, token accounting and cost estimation."""

from dataclasses import dataclass

import pytest

from features.llm.agent import run_agent
from features.llm.tracing import AgentTrace, estimate_cost


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


class TracingClient:
    """Fake client that reports token usage on each completion."""

    model = "gpt-4o"

    def __init__(self, responses, usage, resolved_model="llama-3.3-70b:free"):
        self._responses = list(responses)
        self._usage = usage
        self._resolved_model = resolved_model
        self.last_usage = None
        self.last_model = None

    async def complete(self, messages, tools=None, **kwargs):
        self.last_usage = dict(self._usage)
        self.last_model = self._resolved_model
        return self._responses.pop(0)


class _HistMsg:
    sender = "user"

    def __init__(self, content):
        self.content = content


def test_estimate_cost_known_model():
    # 1M input + 1M output tokens of gpt-4o = 2.5 + 10.0
    assert estimate_cost("gpt-4o", 1_000_000, 1_000_000) == 12.5


def test_estimate_cost_unknown_model_is_free():
    assert estimate_cost("openai/gpt-oss-20b:free", 1000, 1000) == 0.0


def test_agent_trace_accumulates_tokens_and_steps():
    trace = AgentTrace.new(model="openrouter/free")
    trace.record_llm_call(
        12.0, {"prompt_tokens": 100, "completion_tokens": 50}, resolved_model="gpt-4o"
    )
    trace.record_llm_call(8.0, {"prompt_tokens": 30, "completion_tokens": 20})
    trace.record_tool("financial_calculator", 1.5)
    trace.finish()

    data = trace.as_dict()
    assert data["num_llm_calls"] == 2
    assert data["prompt_tokens"] == 130
    assert data["completion_tokens"] == 70
    assert data["total_tokens"] == 200
    assert data["num_tool_calls"] == 1
    assert data["model"] == "openrouter/free"
    assert data["resolved_model"] == "gpt-4o"
    assert data["estimated_cost_usd"] > 0


@pytest.mark.asyncio
async def test_run_agent_produces_trace():
    tool_call = FakeToolCall("c1", FakeFunction("get_current_datetime", "{}"))
    client = TracingClient(
        responses=[FakeMessage(tool_calls=[tool_call]), FakeMessage(content="Готово.")],
        usage={"prompt_tokens": 100, "completion_tokens": 50},
    )

    result = await run_agent([_HistMsg("который час?")], client=client)

    assert result.trace is not None
    assert result.trace.num_llm_calls == 2
    assert result.trace.prompt_tokens == 200
    assert result.trace.model == "gpt-4o"  # configured/requested model
    assert result.trace.resolved_model == "llama-3.3-70b:free"  # model actually served
    assert result.trace.as_dict()["resolved_model"] == "llama-3.3-70b:free"
    assert len(result.trace.steps) == 1
    assert result.trace.duration_ms >= 0
