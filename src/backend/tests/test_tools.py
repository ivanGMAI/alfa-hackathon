"""Tests for the deterministic agent tools and the tool registry."""

import json

from features.llm.tools import execute_tool, get_openai_tools


def _call(name, **arguments):
    return json.loads(execute_tool(name, arguments))


def test_registry_exposes_openai_schema():
    tools = get_openai_tools()
    names = {tool["function"]["name"] for tool in tools}
    assert {
        "financial_calculator",
        "generate_document",
        "get_current_datetime",
    } <= names
    for tool in tools:
        assert tool["type"] == "function"
        assert "parameters" in tool["function"]


def test_financial_margin():
    result = _call("financial_calculator", operation="margin", revenue=100, cost=60)
    assert result["profit"] == 40
    assert result["margin_percent"] == 40.0


def test_financial_markup():
    result = _call(
        "financial_calculator", operation="markup", cost=100, markup_percent=20
    )
    assert result["price"] == 120.0


def test_financial_vat():
    result = _call("financial_calculator", operation="vat", amount=120, rate=20)
    assert result["vat"] == 20.0
    assert result["net"] == 100.0


def test_financial_loan():
    result = _call(
        "financial_calculator",
        operation="loan",
        principal=1000,
        annual_rate=12,
        months=12,
    )
    assert 88 < result["monthly_payment"] < 90
    assert result["total_payment"] > 1000


def test_generate_document_invoice():
    result = _call(
        "generate_document", doc_type="invoice", seller="ООО Ромашка", total="1000"
    )
    assert "СЧЁТ" in result["content"]
    assert "ООО Ромашка" in result["content"]


def test_get_current_datetime():
    result = _call("get_current_datetime")
    assert result["timezone"] == "UTC"
    assert "date" in result


def test_unknown_tool_returns_error_not_exception():
    result = json.loads(execute_tool("does_not_exist", {}))
    assert "error" in result


def test_tool_handler_error_is_captured():
    # Missing required argument for the operation -> handled, not raised.
    result = _call("financial_calculator", operation="margin")
    assert "error" in result
