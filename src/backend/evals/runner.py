"""Eval harness for the agent.

Runs each scenario in ``dataset.jsonl`` through the agent, scores it with two
independent signals — a deterministic tool-selection check and an LLM judge —
then writes a Markdown scorecard. Run with ``make eval`` (needs an API key).

The pure pieces (loading, scoring, aggregation, rendering) are unit-tested with
injectable ``agent_runner`` / ``judge`` callables, so they run without network.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Awaitable, Callable

from pydantic import BaseModel

from evals.judge import JudgeVerdict, judge_answer
from features.llm.agent import AgentResult, run_agent

DATASET_PATH = Path(__file__).parent / "dataset.jsonl"
REPORT_PATH = Path(__file__).parent / "report.md"


class EvalCase(BaseModel):
    id: str
    input: str
    expected_tool: str | None = None
    behavior: str
    rubric: str


class CaseResult(BaseModel):
    id: str
    behavior: str
    tool_ok: bool
    passed: bool
    score: int
    reasoning: str


AgentRunner = Callable[[str], Awaitable[AgentResult]]
Judge = Callable[..., Awaitable[JudgeVerdict]]


def load_dataset(path: Path = DATASET_PATH) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cases.append(EvalCase(**json.loads(line)))
    return cases


def tool_selection_ok(steps, expected_tool: str | None) -> bool:
    used = {step.tool for step in steps}
    if expected_tool is None:
        return len(used) == 0
    return expected_tool in used


class _HistMsg:
    def __init__(self, content: str):
        self.sender = "user"
        self.content = content


async def _default_agent(text: str) -> AgentResult:
    return await run_agent([_HistMsg(text)])


async def evaluate(
    cases: list[EvalCase],
    *,
    agent_runner: AgentRunner = _default_agent,
    judge: Judge = judge_answer,
) -> list[CaseResult]:
    results: list[CaseResult] = []
    for case in cases:
        agent_result = await agent_runner(case.input)
        verdict = await judge(case.input, case.rubric, agent_result.content)
        results.append(
            CaseResult(
                id=case.id,
                behavior=case.behavior,
                tool_ok=tool_selection_ok(agent_result.steps, case.expected_tool),
                passed=verdict.passed,
                score=verdict.score,
                reasoning=verdict.reasoning,
            )
        )
    return results


def aggregate(results: list[CaseResult]) -> dict:
    n = len(results) or 1
    return {
        "total": len(results),
        "pass_rate": round(sum(r.passed for r in results) / n, 3),
        "tool_accuracy": round(sum(r.tool_ok for r in results) / n, 3),
        "avg_score": round(sum(r.score for r in results) / n, 2),
    }


def render_report(results: list[CaseResult], summary: dict) -> str:
    lines = [
        "# Agent Eval Report",
        "",
        f"- Cases: **{summary['total']}**",
        f"- Pass rate: **{summary['pass_rate'] * 100:.0f}%**",
        f"- Tool-selection accuracy: **{summary['tool_accuracy'] * 100:.0f}%**",
        f"- Average judge score: **{summary['avg_score']}/5**",
        "",
        "| Case | Behavior | Tool OK | Passed | Score | Reasoning |",
        "|---|---|:---:|:---:|:---:|---|",
    ]
    for r in results:
        reasoning = r.reasoning.replace("|", " ").replace("\n", " ")[:120]
        lines.append(
            f"| {r.id} | {r.behavior} | {'✅' if r.tool_ok else '❌'} | "
            f"{'✅' if r.passed else '❌'} | {r.score} | {reasoning} |"
        )
    return "\n".join(lines) + "\n"


async def run() -> dict:
    cases = load_dataset()
    results = await evaluate(cases)
    summary = aggregate(results)
    report = render_report(results, summary)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    return summary


if __name__ == "__main__":
    asyncio.run(run())
