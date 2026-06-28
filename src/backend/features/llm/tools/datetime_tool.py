"""Current date/time tool — grounds the model in real time instead of guessing."""

from __future__ import annotations

from datetime import datetime, timezone

from .base import Tool, register


def _get_current_datetime() -> dict:
    now = datetime.now(timezone.utc)
    return {
        "iso": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "timezone": "UTC",
    }


get_current_datetime = register(
    Tool(
        name="get_current_datetime",
        description=(
            "Возвращает текущие дату и время (UTC). Используй, когда нужна актуальная "
            "дата — например, чтобы проставить дату в счёте или письме."
        ),
        parameters={"type": "object", "properties": {}},
        handler=_get_current_datetime,
    )
)
