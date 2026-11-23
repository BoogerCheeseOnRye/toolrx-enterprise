"""
ToolRouter: High-performance deterministic micro tool router for LLM/agent calling.
Zero LLM dependencies, sub-millisecond edge latency, deterministic precision.
"""

import time
from typing import Dict, List, Any, Optional, Set, Union
from .core.schema import ToolDefinition, RouteResult, tokenize_identifier
from .core.trie import TokenIndex
from .core.matcher import DeterministicMatcher

class ToolRouter:
    """
    Zero-LLM deterministic tool router.
    Prunes hundreds of tools down to the exact relevant top-k tools in microseconds,
    slashing prompt token costs and LLM latency while eliminating hallucinations.
    """

    def __init__(self, tools: Optional[List[Union[Dict[str, Any], ToolDefinition]]] = None):
        self.tools: Dict[str, ToolDefinition] = {}
        self.token_index = TokenIndex()
        self.matcher = DeterministicMatcher(self.tools)
        self.default_fallback: List[str] = []

        if tools:
            self.register_tools(tools)

    def register_tool(self, tool: Union[Dict[str, Any], ToolDefinition]) -> ToolDefinition:
        """Register a single tool into the deterministic index."""
        if isinstance(tool, dict):
            tool_def = ToolDefinition.from_dict(tool)
        elif isinstance(tool, ToolDefinition):
            tool_def = tool
        else:
            raise TypeError(f"Expected dict or ToolDefinition, got {type(tool)}")

        self.tools[tool_def.name] = tool_def
        self.token_index.add_tool_tokens(
            tool_name=tool_def.name,
            name_tokens=tool_def.name_tokens,
            desc_tokens=tool_def.desc_tokens,
            param_tokens={tok for p in tool_def.parameters.values() for tok in p.tokens},
            tags=tool_def.tags
        )
        self.matcher.reindex()
        return tool_def

    def register_tools(self, tools: List[Union[Dict[str, Any], ToolDefinition]]) -> None:
        """Register a batch of tools."""
        for t in tools:
            if isinstance(t, dict):
                tool_def = ToolDefinition.from_dict(t)
            elif isinstance(t, ToolDefinition):
                tool_def = t
            else:
                continue
            self.tools[tool_def.name] = tool_def
            self.token_index.add_tool_tokens(
                tool_name=tool_def.name,
                name_tokens=tool_def.name_tokens,
                desc_tokens=tool_def.desc_tokens,
                param_tokens={tok for p in tool_def.parameters.values() for tok in p.tokens},
                tags=tool_def.tags
            )
        self.matcher.reindex()

    def add_rule(self, pattern: str, target_tool: str, boost: float = 10.0) -> None:
        """Add an explicit regex routing rule for deterministic enforcement."""
        self.matcher.add_rule(pattern, target_tool, boost)

    def set_fallback_tools(self, tool_names: List[str]) -> None:
        """Set default fallback tools to return if no tool matches query."""
        self.default_fallback = list(tool_names)

    def route(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 1.0,
        fallback_tools: Optional[List[str]] = None
    ) -> RouteResult:
        """
        Route a user/agent query to the top-k relevant tools in microseconds.
        Returns RouteResult containing selected tools, scores, latency, and token metrics.
        """
        start_ns = time.perf_counter_ns()

        query_tokens = tokenize_identifier(query)

        # Stage 1: Fast Trie & Inverted Token Index lookup (< 15 microseconds)
        base_scores = self.token_index.query_tokens(query_tokens, allow_prefix=True)

        # Stage 2: Deterministic multi-factor scoring (rules, parameters, negations) (< 20 microseconds)
        scores, explanations = self.matcher.match(query, base_scores)

        # Stage 3: Ranking and Filtering
        ranked = sorted(
            [(t, s) for t, s in scores.items() if s >= min_score],
            key=lambda x: x[1],
            reverse=True
        )

        selected = [t for t, _ in ranked[:top_k]]

        # Fallback if no matching tools met min_score
        if not selected:
            effective_fallback = fallback_tools if fallback_tools is not None else self.default_fallback
            selected = [t for t in effective_fallback if t in self.tools][:top_k]

        elapsed_us = (time.perf_counter_ns() - start_ns) / 1_000.0

        # Token savings accounting
        total_prompt_tokens = sum(t.estimated_tokens for t in self.tools.values())
        routed_prompt_tokens = sum(self.tools[t].estimated_tokens for t in selected if t in self.tools)
        tokens_saved = max(0, total_prompt_tokens - routed_prompt_tokens)
        savings_pct = (tokens_saved / total_prompt_tokens * 100.0) if total_prompt_tokens > 0 else 0.0

        return RouteResult(
            query=query,
            selected_tools=selected,
            scores={t: scores.get(t, 0.0) for t in selected},
            all_evaluated_count=len(self.tools),
            selected_count=len(selected),
            latency_microseconds=round(elapsed_us, 2),
            estimated_prompt_tokens_original=total_prompt_tokens,
            estimated_prompt_tokens_routed=routed_prompt_tokens,
            tokens_saved=tokens_saved,
            token_savings_pct=round(savings_pct, 1),
            explanation={t: explanations.get(t, []) for t in selected}
        )

    def prune_tools(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 1.0,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Drop-in pruning utility: takes query and returns original tool definitions
        filtered to top-k relevant tools.
        """
        if tools:
            # Ephemeral routing over provided tools
            temp_router = ToolRouter(tools)
            result = temp_router.route(query, top_k=top_k, min_score=min_score)
            return [temp_router.tools[name].raw_schema for name in result.selected_tools if name in temp_router.tools]

        result = self.route(query, top_k=top_k, min_score=min_score)
        return [self.tools[name].raw_schema for name in result.selected_tools if name in self.tools]

    def register(
        self,
        fn: Optional[Any] = None,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        triggers: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ):
        """
        Decorator or function to register a callable or schema into ToolRouter.
        Supports:
            @router.register(name="tool_name", triggers=["keyword1", "keyword2"])
            def my_tool(): ...
        """
        def decorator(target):
            tool_name = name or getattr(target, "__name__", "unnamed_tool")
            doc = description or getattr(target, "__doc__", "") or ""
            all_tags = list(tags or [])
            if triggers:
                all_tags.extend(triggers)

            tool_def = ToolDefinition(
                name=tool_name,
                description=doc,
                tags=set(all_tags),
                raw_schema={"name": tool_name, "description": doc}
            )
            self.tools[tool_name] = tool_def
            self.token_index.add_tool_tokens(
                tool_name=tool_name,
                name_tokens=tool_def.name_tokens,
                desc_tokens=tool_def.desc_tokens,
                param_tokens=set(all_tags),
                tags=tool_def.tags
            )
            self.matcher.reindex()
            return target

        if fn is not None:
            return decorator(fn)
        return decorator

    def match(self, query: str, top_k: int = 1) -> Optional[RouteResult]:
        """Convenience alias for route(query, top_k)."""
        return self.route(query, top_k=top_k)
