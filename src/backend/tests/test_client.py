"""Tests for the streaming reconstruction helper in the LLM client."""

from types import SimpleNamespace

import pytest

from features.llm.client import LLMClient, _reconstruct_message


def _chunk(content=None, tool_calls=None, model="test-model", usage=None):
    delta = SimpleNamespace(content=content, tool_calls=tool_calls)
    choices = (
        []
        if (content is None and tool_calls is None)
        else [SimpleNamespace(delta=delta)]
    )
    return SimpleNamespace(model=model, choices=choices, usage=usage)


def _tc(index, *, id=None, name=None, arguments=None):
    return SimpleNamespace(
        index=index,
        id=id,
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def _patch_stream(client, chunks):
    async def _aiter():
        for chunk in chunks:
            yield chunk

    async def _create(**kwargs):
        return _aiter()

    client._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=_create))
    )


def test_reconstruct_plain_content():
    msg = _reconstruct_message(["Hello", " world"], {})
    assert msg.content == "Hello world"
    assert msg.tool_calls is None


def test_reconstruct_tool_call_from_streamed_fragments():
    # Tool-call arguments arrive split across several streamed chunks.
    tool_calls = {
        0: {
            "id": "call_1",
            "name": "financial_calculator",
            "arguments": '{"operation": "margin"}',
        }
    }
    msg = _reconstruct_message([], tool_calls)

    assert msg.content is None
    assert len(msg.tool_calls) == 1
    call = msg.tool_calls[0]
    assert call.id == "call_1"
    assert call.function.name == "financial_calculator"
    assert call.function.arguments == '{"operation": "margin"}'


def test_reconstruct_keeps_tool_calls_in_index_order():
    tool_calls = {
        1: {"id": "b", "name": "get_current_datetime", "arguments": "{}"},
        0: {"id": "a", "name": "financial_calculator", "arguments": "{}"},
    }
    msg = _reconstruct_message([], tool_calls)

    assert [c.id for c in msg.tool_calls] == ["a", "b"]


def test_reconstruct_skips_unnamed_tool_slots():
    msg = _reconstruct_message([], {0: {"id": None, "name": "", "arguments": ""}})
    assert msg.tool_calls is None


def test_reconstruct_falls_back_to_index_for_missing_id():
    msg = _reconstruct_message(
        [], {3: {"id": None, "name": "get_current_datetime", "arguments": ""}}
    )
    assert msg.tool_calls[0].id == "call_3"
    assert msg.tool_calls[0].function.arguments == "{}"


@pytest.mark.asyncio
async def test_stream_yields_content_tokens_and_captures_usage():
    client = LLMClient()
    _patch_stream(
        client,
        [
            _chunk(content="Привет"),
            _chunk(content=", мир"),
            _chunk(usage=SimpleNamespace(prompt_tokens=12, completion_tokens=4)),
        ],
    )

    events = [(kind, payload) async for kind, payload in client.stream([])]

    tokens = [p for k, p in events if k == "token"]
    assert tokens == ["Привет", ", мир"]
    kind, message = events[-1]
    assert kind == "message"
    assert message.content == "Привет, мир"
    assert message.tool_calls is None
    assert client.last_usage == {"prompt_tokens": 12, "completion_tokens": 4}
    assert client.last_model == "test-model"


@pytest.mark.asyncio
async def test_stream_accumulates_tool_call_fragments():
    client = LLMClient()
    _patch_stream(
        client,
        [
            _chunk(
                tool_calls=[
                    _tc(0, id="call_1", name="financial_calculator", arguments='{"op')
                ]
            ),
            _chunk(tool_calls=[_tc(0, arguments='eration": "margin"}')]),
            _chunk(usage=SimpleNamespace(prompt_tokens=20, completion_tokens=8)),
        ],
    )

    events = [(kind, payload) async for kind, payload in client.stream([])]

    assert all(kind != "token" for kind, _ in events[:-1])
    _, message = events[-1]
    assert message.content is None
    assert len(message.tool_calls) == 1
    call = message.tool_calls[0]
    assert call.id == "call_1"
    assert call.function.name == "financial_calculator"
    assert call.function.arguments == '{"operation": "margin"}'
