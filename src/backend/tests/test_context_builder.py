"""Tests for the role-based context builder."""

from features.llm.context_builder import build_messages, count_tokens


class FakeMessage:
    def __init__(self, sender: str, content: str):
        self.sender = sender
        self.content = content


def test_count_tokens():
    assert count_tokens("") >= 0
    assert count_tokens("hello world, this is a test") >= 1


def test_system_prompt_is_first_and_roles_are_mapped():
    history = [FakeMessage("user", "Привет"), FakeMessage("llm", "Здравствуйте")]

    messages = build_messages(history)

    assert messages[0]["role"] == "system"
    assert "ИИ-помощник" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "Привет"}
    assert messages[2] == {"role": "assistant", "content": "Здравствуйте"}


def test_history_stays_in_chronological_order():
    history = [
        FakeMessage("user", "first"),
        FakeMessage("llm", "second"),
        FakeMessage("user", "third"),
    ]

    contents = [m["content"] for m in build_messages(history)[1:]]

    assert contents == ["first", "second", "third"]


def test_token_budget_keeps_only_recent_turns():
    history = [FakeMessage("user", "x" * 4000) for _ in range(50)]

    messages = build_messages(history, max_tokens=200)

    assert messages[0]["role"] == "system"
    assert 2 <= len(messages) < 50  # system + at most a few recent turns
