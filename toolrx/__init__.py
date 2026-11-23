"""
ToolRx: Commercial Deterministic Micro Tool Router for LLM / Tool Calling.
Zero LLM Dependencies. Sub-millisecond Edge Latency. 100% Deterministic.
"""

from .router import ToolRouter
from .core.schema import ToolDefinition, ToolParameter, RouteResult
from .core.trie import TokenIndex, PrefixTrie
from .core.matcher import DeterministicMatcher
from .adapters.openai_adapter import ToolRxOpenAI
from .adapters.anthropic_adapter import ToolRxAnthropic

__version__ = "1.0.0"
__author__ = "ToolRx Engineering Team"
__license__ = "Business Source License 1.1 / Commercial"

__all__ = [
    "ToolRouter",
    "ToolDefinition",
    "ToolParameter",
    "RouteResult",
    "TokenIndex",
    "PrefixTrie",
    "DeterministicMatcher",
    "ToolRxOpenAI",
    "ToolRxAnthropic",
]
