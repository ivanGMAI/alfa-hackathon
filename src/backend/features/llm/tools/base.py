"""Tool registry for the agent.

A tool is a deterministic Python function exposed to the LLM via the OpenAI
function-calling schema. The agent decides *when* to call a tool; this module is
responsible for describing the tools to the model and executing them safely.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict  # JSON Schema describing the function arguments
    handler: Callable[..., object]

    def to_openai(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


_REGISTRY: dict[str, Tool] = {}


def register(tool: Tool) -> Tool:
    _REGISTRY[tool.name] = tool
    return tool


def get_openai_tools() -> list[dict]:
    """Return all registered tools in the OpenAI ``tools`` format."""
    return [tool.to_openai() for tool in _REGISTRY.values()]


def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool and return its result as a JSON string.

    Tool failures are converted into a structured error payload so a single bad
    call never crashes the agent loop — the model can read the error and recover.
    """
    tool = _REGISTRY.get(name)
    if tool is None:
        return json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)

    try:
        result = tool.handler(**arguments)
    except Exception as exc:  # noqa: BLE001 — surface any tool error to the model
        return json.dumps({"error": str(exc)}, ensure_ascii=False)

    if isinstance(result, str):
        return result
    return json.dumps(result, ensure_ascii=False, default=str)
