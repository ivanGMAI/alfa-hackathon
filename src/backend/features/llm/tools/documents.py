"""Document drafting from structured fields."""

from __future__ import annotations

from .base import Tool, register


def _generate_document(doc_type: str, **fields) -> dict:
    dt = doc_type.lower()

    if dt == "invoice":
        items = fields.get("items", "")
        total = fields.get("total", "")
        content = (
            f"СЧЁТ на оплату\n"
            f"От: {fields.get('seller', '—')}\n"
            f"Кому: {fields.get('buyer', '—')}\n"
            f"Дата: {fields.get('date', '—')}\n\n"
            f"Позиции:\n{items}\n\n"
            f"Итого к оплате: {total}"
        )
    elif dt == "letter":
        content = (
            f"Уважаемый(ая) {fields.get('recipient', 'клиент')}!\n\n"
            f"{fields.get('body', '')}\n\n"
            f"С уважением,\n{fields.get('sender', '')}"
        )
    elif dt == "contract":
        content = (
            f"ДОГОВОР {fields.get('subject', '')}\n\n"
            f"Стороны: {fields.get('party_a', '—')} и {fields.get('party_b', '—')}.\n"
            f"Предмет: {fields.get('subject', '—')}.\n"
            f"Сумма: {fields.get('amount', '—')}.\n"
            f"Срок: {fields.get('term', '—')}."
        )
    else:
        return {"error": f"Unknown doc_type: {doc_type}"}

    return {"doc_type": dt, "content": content}


generate_document = register(
    Tool(
        name="generate_document",
        description=(
            "Формирует черновик делового документа из переданных полей: счёт (invoice), "
            "деловое письмо (letter) или договор (contract). Возвращает готовый текст."
        ),
        parameters={
            "type": "object",
            "properties": {
                "doc_type": {
                    "type": "string",
                    "enum": ["invoice", "letter", "contract"],
                    "description": "Тип документа",
                },
                "seller": {"type": "string"},
                "buyer": {"type": "string"},
                "date": {"type": "string"},
                "items": {"type": "string", "description": "Позиции счёта"},
                "total": {"type": "string"},
                "recipient": {"type": "string"},
                "sender": {"type": "string"},
                "body": {"type": "string", "description": "Текст письма"},
                "subject": {"type": "string"},
                "party_a": {"type": "string"},
                "party_b": {"type": "string"},
                "amount": {"type": "string"},
                "term": {"type": "string"},
            },
            "required": ["doc_type"],
        },
        handler=_generate_document,
    )
)
