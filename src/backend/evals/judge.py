"""LLM-as-judge: scores an agent answer against a per-case rubric."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, ValidationError

from features.llm.client import LLMClient


class JudgeVerdict(BaseModel):
    passed: bool
    score: int  # 1..5
    reasoning: str


_JUDGE_SYSTEM = (
    "Ты — строгий и объективный оценщик качества ответов ИИ-ассистента для малого "
    "бизнеса. Оцени, насколько ответ соответствует критерию. Будь требователен."
)


def _build_prompt(user_input: str, rubric: str, answer: str) -> list[dict]:
    user = (
        f"Запрос пользователя:\n{user_input}\n\n"
        f"Критерий оценки:\n{rubric}\n\n"
        f"Ответ ассистента:\n{answer}\n\n"
        "Верни СТРОГО JSON без пояснений вокруг: "
        '{"passed": true/false, "score": 1-5, "reasoning": "кратко почему"}'
    )
    return [
        {"role": "system", "content": _JUDGE_SYSTEM},
        {"role": "user", "content": user},
    ]


def parse_verdict(text: str) -> JudgeVerdict:
    """Tolerantly extract a JSON verdict from the judge's reply."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return JudgeVerdict(
            passed=False, score=1, reasoning="Не удалось разобрать ответ судьи."
        )
    try:
        return JudgeVerdict(**json.loads(match.group(0)))
    except (json.JSONDecodeError, ValidationError) as exc:
        return JudgeVerdict(passed=False, score=1, reasoning=f"Ошибка разбора: {exc}")


async def judge_answer(
    user_input: str,
    rubric: str,
    answer: str,
    *,
    client: LLMClient | None = None,
) -> JudgeVerdict:
    client = client or LLMClient()
    message = await client.complete(
        _build_prompt(user_input, rubric, answer), temperature=0
    )
    return parse_verdict(message.content or "")
