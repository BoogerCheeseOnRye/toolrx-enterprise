"""
ToolRx Commercial: Deterministic Micro Tool Router for LLM / Tool Calling.
Zero LLM Dependencies. Sub-millisecond Edge Latency. 100% Deterministic.

This commercial package wraps the upstream boogercheeseonrye/toolrx hashing
engine and adds enterprise adapters, gateway server, and telemetry.
"""

import os
import sys

# Ensure upstream sibling modules (tokhash, router) are importable
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from .compat import ToolRouter, route, tool

# Enterprise adapters (commercial-only)
try:
    from .adapters.openai_adapter import ToolRxOpenAI
    from .adapters.anthropic_adapter import ToolRxAnthropic
except Exception:
    ToolRxOpenAI = None
    ToolRxAnthropic = None

__version__ = "1.1.0"
__author__ = "BoogerCheeseOnRye"
__license__ = "Business Source License 1.1 / Commercial"

__all__ = [
    "ToolRouter",
    "route",
    "tool",
    "ToolRxOpenAI",
    "ToolRxAnthropic",
]
