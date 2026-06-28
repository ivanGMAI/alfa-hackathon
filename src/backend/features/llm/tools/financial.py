"""Financial calculations for the small-business assistant."""

from __future__ import annotations

from .base import Tool, register


def _financial_calculator(operation: str, **params) -> dict:
    op = operation.lower()

    if op == "margin":
        revenue = float(params["revenue"])
        cost = float(params["cost"])
        profit = revenue - cost
        margin_percent = (profit / revenue * 100) if revenue else 0.0
        return {
            "operation": "margin",
            "profit": round(profit, 2),
            "margin_percent": round(margin_percent, 2),
        }

    if op == "markup":
        cost = float(params["cost"])
        markup_percent = float(params["markup_percent"])
        price = cost * (1 + markup_percent / 100)
        return {
            "operation": "markup",
            "price": round(price, 2),
            "profit": round(price - cost, 2),
        }

    if op == "vat":
        gross = float(params["amount"])
        rate = float(params.get("rate", 20))
        vat = gross * rate / (100 + rate)
        return {
            "operation": "vat",
            "gross": round(gross, 2),
            "vat": round(vat, 2),
            "net": round(gross - vat, 2),
            "rate": rate,
        }

    if op == "loan":
        principal = float(params["principal"])
        annual_rate = float(params["annual_rate"])
        months = int(params["months"])
        monthly_rate = annual_rate / 100 / 12
        if monthly_rate == 0:
            payment = principal / months
        else:
            factor = (1 + monthly_rate) ** months
            payment = principal * monthly_rate * factor / (factor - 1)
        total = payment * months
        return {
            "operation": "loan",
            "monthly_payment": round(payment, 2),
            "total_payment": round(total, 2),
            "overpayment": round(total - principal, 2),
        }

    return {"error": f"Unknown operation: {operation}"}


financial_calculator = register(
    Tool(
        name="financial_calculator",
        description=(
            "Выполняет точные финансовые расчёты для малого бизнеса: маржа (margin), "
            "цена с наценкой (markup), выделение НДС (vat) и аннуитетный платёж по "
            "кредиту (loan). Используй вместо ручного счёта в уме."
        ),
        parameters={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["margin", "markup", "vat", "loan"],
                    "description": "Тип расчёта",
                },
                "revenue": {"type": "number", "description": "Выручка (для margin)"},
                "cost": {
                    "type": "number",
                    "description": "Себестоимость (для margin и markup)",
                },
                "markup_percent": {
                    "type": "number",
                    "description": "Наценка в процентах (для markup)",
                },
                "amount": {
                    "type": "number",
                    "description": "Сумма с НДС (для vat)",
                },
                "rate": {
                    "type": "number",
                    "description": "Ставка НДС в процентах, по умолчанию 20 (для vat)",
                },
                "principal": {
                    "type": "number",
                    "description": "Сумма кредита (для loan)",
                },
                "annual_rate": {
                    "type": "number",
                    "description": "Годовая ставка в процентах (для loan)",
                },
                "months": {
                    "type": "integer",
                    "description": "Срок кредита в месяцах (для loan)",
                },
            },
            "required": ["operation"],
        },
        handler=_financial_calculator,
    )
)
