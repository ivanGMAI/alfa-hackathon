import json
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

import features.messages.crud.message as crud
import features.messages.mappers.message_builder as builder
from features.chats.validators import check_chat_permission, get_chat_or_404
from features.llm.agent import AgentStep, run_agent, run_agent_events
from features.llm.guardrails import REFUSAL_MESSAGE, evaluate_input
from features.llm.tracing import log_security_event
from features.messages.schemas import (
    AgentStepSchema,
    MessageCreate,
    MessageRead,
    SourceSchema,
)
from features.rag import RetrievedChunk, search_chat_documents, search_knowledge
from shared.enums import SenderEnum

FALLBACK_ANSWER = (
    "Извините, не удалось сформировать ответ. Попробуйте переформулировать запрос."
)

# How many grounding chunks to inject into the agent context at most.
MAX_CONTEXT_CHUNKS = 6


async def _retrieve_grounding(
    session: AsyncSession, chat_id: int, query: str
) -> list[RetrievedChunk]:
    """Gather grounding chunks: the chat's uploaded documents first (most
    specific), then the global knowledge base, capped to a small budget."""
    doc_chunks = await search_chat_documents(session, chat_id, query)
    kb_chunks = await search_knowledge(session, query)
    return (doc_chunks + kb_chunks)[:MAX_CONTEXT_CHUNKS]


def _steps_to_schema(steps: list[AgentStep]) -> list[AgentStepSchema]:
    return [
        AgentStepSchema(tool=step.tool, arguments=step.arguments, result=step.result)
        for step in steps
    ]


def _sources_to_schema(chunks: list[RetrievedChunk]) -> list[SourceSchema]:
    return [SourceSchema(title=chunk.title, source=chunk.source) for chunk in chunks]


async def _chronological_history(session: AsyncSession, chat_id: int):
    messages = await crud.get_messages_for_window(session, chat_id)
    return list(
        reversed(messages)
    )  # crud returns newest-first; agent wants oldest-first


async def send_message(
    session: AsyncSession,
    message_create: MessageCreate,
    user_id: int,
) -> dict[str, MessageRead]:
    chat = await get_chat_or_404(session, message_create.chat_id)
    check_chat_permission(chat.user_id, user_id)

    user_message = await crud.create_message(session, message_create, SenderEnum.USER)

    guard = evaluate_input(message_create.content)
    if guard.flagged:
        log_security_event(guard.category, guard.matched, user_id)
        refusal = await crud.create_message(
            session,
            MessageCreate(chat_id=message_create.chat_id, content=REFUSAL_MESSAGE),
            SenderEnum.LLM,
        )
        return {
            "user_message": builder.build_message_schema(user_message),
            "llm_message": builder.build_message_schema(refusal),
        }

    history = await _chronological_history(session, message_create.chat_id)
    chunks = await _retrieve_grounding(
        session, message_create.chat_id, message_create.content
    )

    result = await run_agent(history, knowledge=[chunk.content for chunk in chunks])

    llm_message = await crud.create_message(
        session,
        MessageCreate(
            chat_id=message_create.chat_id,
            content=result.content or FALLBACK_ANSWER,
        ),
        SenderEnum.LLM,
    )

    llm_read = builder.build_message_schema(llm_message)
    llm_read.steps = _steps_to_schema(result.steps)
    llm_read.sources = _sources_to_schema(chunks)

    return {
        "user_message": builder.build_message_schema(user_message),
        "llm_message": llm_read,
    }


def _sse(event: str, data: dict | list) -> str:
    return (
        f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
    )


def _chunk_text(text: str) -> list[str]:
    """Split text into word-sized chunks for a progressive (typing) UI effect."""
    words = text.split(" ")
    return [word if i == 0 else " " + word for i, word in enumerate(words)]


async def stream_message(
    session: AsyncSession,
    message_create: MessageCreate,
    user_id: int,
) -> AsyncIterator[str]:
    """Server-Sent Events stream: user_message -> step* -> token* -> done."""
    chat = await get_chat_or_404(session, message_create.chat_id)
    check_chat_permission(chat.user_id, user_id)

    user_message = await crud.create_message(session, message_create, SenderEnum.USER)
    yield _sse(
        "user_message",
        builder.build_message_schema(user_message).model_dump(mode="json"),
    )

    guard = evaluate_input(message_create.content)
    if guard.flagged:
        log_security_event(guard.category, guard.matched, user_id)
        for chunk in _chunk_text(REFUSAL_MESSAGE):
            yield _sse("token", {"delta": chunk})
        refusal = await crud.create_message(
            session,
            MessageCreate(chat_id=message_create.chat_id, content=REFUSAL_MESSAGE),
            SenderEnum.LLM,
        )
        yield _sse(
            "done", builder.build_message_schema(refusal).model_dump(mode="json")
        )
        return

    history = await _chronological_history(session, message_create.chat_id)
    retrieved = await _retrieve_grounding(
        session, message_create.chat_id, message_create.content
    )
    if retrieved:
        yield _sse(
            "sources",
            [s.model_dump() for s in _sources_to_schema(retrieved)],
        )

    steps: list[AgentStep] = []
    content = ""
    streamed_any = False
    async for kind, payload in run_agent_events(
        history, knowledge=[chunk.content for chunk in retrieved], stream=True
    ):
        if kind == "step":
            steps.append(payload)
            yield _sse(
                "step",
                {
                    "tool": payload.tool,
                    "arguments": payload.arguments,
                    "result": payload.result,
                },
            )
        elif kind == "token":
            streamed_any = True
            yield _sse("token", {"delta": payload})
        else:
            content = payload or FALLBACK_ANSWER

    # If the model produced no streamed tokens (e.g. empty answer -> fallback),
    # still emit the text so the UI shows something.
    if not streamed_any:
        for chunk in _chunk_text(content):
            yield _sse("token", {"delta": chunk})

    llm_message = await crud.create_message(
        session,
        MessageCreate(chat_id=message_create.chat_id, content=content),
        SenderEnum.LLM,
    )
    llm_read = builder.build_message_schema(llm_message)
    llm_read.sources = _sources_to_schema(retrieved)
    llm_read.steps = _steps_to_schema(steps)
    yield _sse("done", llm_read.model_dump(mode="json"))
