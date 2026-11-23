"""
Generic adapter utilities for LLM orchestration frameworks (LangChain, LiteLLM, LlamaIndex).
"""

from typing import Dict, List, Any, Callable
from ..router import ToolRouter

class GenericToolAdapter:
    """Utility to adapt arbitrary callable tools or schema definitions."""

    @staticmethod
    def wrap_agent_toolset(tools: List[Any], schema_extractor: Callable[[Any], Dict[str, Any]], top_k: int = 5):
        """Wrap an arbitrary list of agent tools with routing on invocation."""
        tool_map = {schema_extractor(t).get("name", str(i)): t for i, t in enumerate(tools)}
        schemas = [schema_extractor(t) for t in tools]
        router = ToolRouter(schemas)

        def get_active_tools(query: str) -> List[Any]:
            result = router.route(query, top_k=top_k)
            return [tool_map[name] for name in result.selected_tools if name in tool_map]

        return get_active_tools
