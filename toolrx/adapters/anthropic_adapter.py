"""
Anthropic Messages API adapter for toolrx.
Prunes tool schemas before sending to Claude models.
"""

from typing import Dict, List, Any, Optional
from ..compat import ToolRouter

class ToolRxAnthropic:
    """Drop-in adapter for Anthropic Messages payloads."""

    @staticmethod
    def extract_last_user_query(messages: List[Dict[str, Any]]) -> str:
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content")
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
                    return " ".join(texts)
        return ""

    @classmethod
    def optimize_payload(
        cls,
        payload: Dict[str, Any],
        top_k: int = 5,
        min_score: float = 1.0,
        router: Optional[ToolRouter] = None
    ) -> Dict[str, Any]:
        """Takes Anthropic payload with tools and returns optimized payload."""
        tools = payload.get("tools")
        if not tools or len(tools) <= top_k:
            return payload

        messages = payload.get("messages", [])
        query = cls.extract_last_user_query(messages)
        if not query:
            return payload

        active_router = router if router is not None else ToolRouter(tools)
        pruned_tools = active_router.prune_tools(query, top_k=top_k, min_score=min_score)

        optimized = dict(payload)
        optimized["tools"] = pruned_tools
        return optimized
