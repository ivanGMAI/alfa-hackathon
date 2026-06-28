"""Lightweight tracing & structured logging for agent runs.

Captures per-run observability — model, number of LLM calls, token usage, tool
steps, latency and an estimated cost — and emits it as a single structured JSON
log line. No external dependency required; Sentry is wired separately and gated
on a DSN being configured.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from time import perf_counter
from uuid import uuid4

# Prices in USD per 1M tokens (input, output). Extend as needed; unknown -> free.
MODEL_PRICES: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-4.1": (2.0, 8.0),
    "claude": (3.0, 15.0),
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    prices = next(
        (v for k, v in MODEL_PRICES.items() if k in model.lower()), (0.0, 0.0)
    )
    cost = (
        prompt_tokens / 1_000_000 * prices[0]
        + completion_tokens / 1_000_000 * prices[1]
    )
    return round(cost, 6)


@dataclass
class StepTrace:
    tool: str
    duration_ms: float


@dataclass
class AgentTrace:
    request_id: str
    model: str
    num_llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    steps: list[StepTrace] = field(default_factory=list)
    duration_ms: float = 0.0
    finish_reason: str = "completed"
    resolved_model: str | None = None  # model the API actually served the request
    _start: float = field(default_factory=perf_counter, repr=False)

    @classmethod
    def new(cls, model: str) -> "AgentTrace":
        return cls(request_id=uuid4().hex[:12], model=model)

    def record_llm_call(
        self,
        duration_ms: float,
        usage: dict | None,
        resolved_model: str | None = None,
    ) -> None:
        self.num_llm_calls += 1
        if usage:
            self.prompt_tokens += int(usage.get("prompt_tokens") or 0)
            self.completion_tokens += int(usage.get("completion_tokens") or 0)
        if resolved_model:
            self.resolved_model = resolved_model

    def record_tool(self, tool: str, duration_ms: float) -> None:
        self.steps.append(StepTrace(tool=tool, duration_ms=round(duration_ms, 1)))

    def finish(self, finish_reason: str | None = None) -> None:
        if finish_reason:
            self.finish_reason = finish_reason
        self.duration_ms = round((perf_counter() - self._start) * 1000, 1)

    @property
    def estimated_cost_usd(self) -> float:
        # Price against the model that actually served the request (e.g. when the
        # configured model is a router like "openrouter/free").
        model = self.resolved_model or self.model
        return estimate_cost(model, self.prompt_tokens, self.completion_tokens)

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "model": self.model,
            "resolved_model": self.resolved_model or self.model,
            "num_llm_calls": self.num_llm_calls,
            "num_tool_calls": len(self.steps),
            "tools": [step.tool for step in self.steps],
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "duration_ms": self.duration_ms,
            "finish_reason": self.finish_reason,
        }


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"level": record.levelname, "event": record.getMessage()}
        data = getattr(record, "data", None)
        if data:
            payload.update(data)
        return json.dumps(payload, ensure_ascii=False, default=str)


_logger = logging.getLogger("agent")
if not _logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(_JsonFormatter())
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False


def log_trace(trace: AgentTrace) -> None:
    _logger.info("agent_run", extra={"data": trace.as_dict()})


def log_security_event(
    category: str, matched: list[str], user_id: int | None = None
) -> None:
    _logger.warning(
        "guardrail_blocked",
        extra={"data": {"category": category, "matched": matched, "user_id": user_id}},
    )
