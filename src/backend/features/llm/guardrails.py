"""Prompt-injection / jailbreak guardrails.

Deterministic, dependency-free checks run *before* the user input reaches the
model (and optionally on the model output). The goal is not perfect security but
a demonstrable first line of defense that is cheap, testable, and logged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

REFUSAL_MESSAGE = (
    "Извините, но я не могу выполнить этот запрос: он похож на попытку обойти мои "
    "инструкции. Я готов помочь с бизнес-задачами — финансами, документами, "
    "маркетингом или операционными вопросами."
)

# Curated, high-precision patterns (RU + EN) for known injection / jailbreak attempts.
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|any\s+)?(previous|prior|above|the)\s+instructions",
    r"disregard\s+(all\s+|the\s+|your\s+)?(previous\s+)?(instructions|system\s+prompt)",
    r"forget\s+(all\s+|everything\s+|your\s+)?(previous\s+)?instructions",
    r"(reveal|show|print|repeat|tell\s+me)\s+(me\s+)?(your\s+)?(system\s+)?prompt",
    r"what\s+(is|are)\s+your\s+(system\s+)?(prompt|instructions)",
    r"you\s+are\s+now\s+(an?\s+)?(unrestricted|jailbroken|dan)\b",
    r"\bdo\s+anything\s+now\b",
    r"игнорируй\s+(все\s+|любые\s+)?(предыдущие\s+)?(инструкции|указания)",
    r"забудь\s+(все\s+|свои\s+)?(предыдущие\s+)?инструкции",
    r"(покажи|раскрой|выведи|повтори)\s+(свой\s+|мне\s+)?(системный\s+)?промпт",
    r"твой\s+системный\s+промпт",
    r"ты\s+теперь\s+(не\s+\w+|без\s+ограничений)",
]

_COMPILED = [re.compile(pattern, re.IGNORECASE) for pattern in _INJECTION_PATTERNS]

# A distinctive opening phrase of the system prompt; if it shows up in output, it leaked.
_SYSTEM_PROMPT_MARKER = "виртуальный ИИ-помощник для владельцев малого бизнеса"


@dataclass
class GuardrailResult:
    flagged: bool
    category: str | None = None
    matched: list[str] = field(default_factory=list)


def evaluate_input(text: str) -> GuardrailResult:
    """Check user input for prompt-injection / jailbreak attempts."""
    matched = [p.pattern for p in _COMPILED if p.search(text)]
    if matched:
        return GuardrailResult(
            flagged=True, category="prompt_injection", matched=matched
        )
    return GuardrailResult(flagged=False)


def evaluate_output(text: str) -> GuardrailResult:
    """Check model output for a leaked system prompt."""
    if _SYSTEM_PROMPT_MARKER.lower() in text.lower():
        return GuardrailResult(
            flagged=True,
            category="system_prompt_leak",
            matched=[_SYSTEM_PROMPT_MARKER],
        )
    return GuardrailResult(flagged=False)
