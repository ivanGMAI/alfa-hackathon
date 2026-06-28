"""Builds the role-based message array sent to the chat-completions API.

Replaces the old "mash everything into one user string" approach with a proper
``[{system}, {user}, {assistant}, ...]`` conversation, trimmed to a token budget
that keeps the most recent turns.
"""

from __future__ import annotations

from features.llm.system_prompt import SYSTEM_PROMPT
from shared.enums import SenderEnum


def count_tokens(text: str) -> int:
    """Count tokens with tiktoken when available, else a cheap heuristic."""
    try:
        import tiktoken

        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:  # noqa: BLE001 — tiktoken is optional, fall back gracefully
        return max(1, len(text) // 4)


def _role_for(sender) -> str:
    value = sender.value if isinstance(sender, SenderEnum) else str(sender)
    return "user" if value == SenderEnum.USER.value else "assistant"


def _knowledge_message(knowledge: list[str]) -> dict:
    block = "\n\n".join(f"[{i + 1}] {chunk}" for i, chunk in enumerate(knowledge))
    return {
        "role": "system",
        "content": (
            "Релевантная информация из базы знаний. Используй её для ответа и "
            "ссылайся на источники в формате [n], если они помогли:\n\n" + block
        ),
    }


def build_messages(
    history,
    system_prompt: str = SYSTEM_PROMPT,
    max_tokens: int = 120_000,
    knowledge: list[str] | None = None,
) -> list[dict]:
    """Assemble the chat messages.

    ``history`` is expected in chronological order (oldest first). The most recent
    turns are kept within ``max_tokens``; older turns are dropped first. When
    ``knowledge`` chunks are provided, they are injected as a system message (RAG).
    """
    prelude: list[dict] = [{"role": "system", "content": system_prompt.strip()}]
    if knowledge:
        prelude.append(_knowledge_message(knowledge))

    used = sum(count_tokens(message["content"]) for message in prelude)
    selected: list[dict] = []

    for message in reversed(history):  # newest first, so we keep recent context
        entry = {"role": _role_for(message.sender), "content": message.content}
        tokens = count_tokens(message.content)
        if used + tokens > max_tokens and selected:
            break
        used += tokens
        selected.append(entry)

    selected.reverse()  # back to chronological order
    return [*prelude, *selected]
