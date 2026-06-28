"""Tests for the eval harness — deterministic pieces with injected fakes."""

import pytest

from evals.judge import parse_verdict
from evals.runner import (
    EvalCase,
    aggregate,
    evaluate,
    load_dataset,
    render_report,
    tool_selection_ok,
)
from features.llm.agent import AgentResult, AgentStep


def test_dataset_loads_and_is_well_formed():
    cases = load_dataset()
    assert len(cases) >= 6
    ids = {c.id for c in cases}
    assert "prompt_injection" in ids
    injection = next(c for c in cases if c.id == "prompt_injection")
    assert injection.behavior == "refuse"


def test_tool_selection_ok():
    steps = [AgentStep("financial_calculator", {}, "{}")]
    assert tool_selection_ok(steps, "financial_calculator")
    assert not tool_selection_ok(steps, "generate_document")
    assert not tool_selection_ok(steps, None)  # expected no tool but one was used
    assert tool_selection_ok([], None)  # expected no tool, none used


def test_parse_verdict_clean():
    verdict = parse_verdict('{"passed": true, "score": 5, "reasoning": "ок"}')
    assert verdict.passed and verdict.score == 5


def test_parse_verdict_with_surrounding_noise():
    verdict = parse_verdict(
        'Оценка: {"passed": false, "score": 2, "reasoning": "плохо"}.'
    )
    assert not verdict.passed and verdict.score == 2


def test_parse_verdict_garbage_falls_back():
    verdict = parse_verdict("здесь нет json")
    assert verdict.passed is False and verdict.score == 1


@pytest.mark.asyncio
async def test_evaluate_aggregate_and_report():
    cases = [
        EvalCase(
            id="calc",
            input="calc",
            expected_tool="financial_calculator",
            behavior="tool_use",
            rubric="r",
        ),
        EvalCase(
            id="advice",
            input="advice",
            expected_tool=None,
            behavior="answer",
            rubric="r",
        ),
    ]

    async def fake_agent(text):
        if text == "calc":
            return AgentResult(
                content="40%", steps=[AgentStep("financial_calculator", {}, "{}")]
            )
        return AgentResult(content="советы", steps=[])

    async def fake_judge(user_input, rubric, answer):
        from evals.judge import JudgeVerdict

        return JudgeVerdict(passed=True, score=4, reasoning="ok")

    results = await evaluate(cases, agent_runner=fake_agent, judge=fake_judge)
    assert len(results) == 2
    assert all(r.tool_ok for r in results)

    summary = aggregate(results)
    assert summary["pass_rate"] == 1.0
    assert summary["tool_accuracy"] == 1.0
    assert summary["avg_score"] == 4.0

    report = render_report(results, summary)
    assert "calc" in report and "advice" in report
    assert "Pass rate" in report
