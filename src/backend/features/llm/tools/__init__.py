"""Agent tools. Importing the submodules registers each tool in the registry."""

from .base import Tool, execute_tool, get_openai_tools, register

# Importing the submodules registers each tool in the registry as a side effect.
from . import datetime_tool  # noqa: F401
from . import documents  # noqa: F401
from . import financial  # noqa: F401

__all__ = ["Tool", "execute_tool", "get_openai_tools", "register"]
