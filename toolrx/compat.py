"""
ToolRx Commercial Package – Public API Compatibility Layer

Wraps upstream boogercheeseonrye/toolrx hashing engine into the ToolRouter
class used by commercial test suite and enterprise adapters.
"""

import os
import sys
import re
import json
import time
from typing import Callable, Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

# Ensure upstream sibling modules (tokhash, router) are importable
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from tokhash import embed, dot, _DIM
from router import route as _upstream_route


@dataclass
class RouteResult:
    """Result returned by ToolRouter.route()"""
    query: str
    selected_tools: List[str]
    scores: Dict[str, float]
    confidence: float
    token_savings_pct: float
    args: Dict = field(default_factory=dict)
    explanation: Dict[str, List[str]] = field(default_factory=dict)
    latency_microseconds: float = 0.0
    all_evaluated_count: int = 0
    selected_count: int = 0
    estimated_prompt_tokens_original: int = 0
    estimated_prompt_tokens_routed: int = 0

    def __getitem__(self, key):
        return getattr(self, key)


@dataclass
class ToolDefinition:
    name: str
    func: Callable
    triggers: List[str]
    description: str = ""
    params: List[Dict] = field(default_factory=list)
    schema: Dict = field(default_factory=dict)
    patterns: List[re.Pattern] = field(default_factory=list)

    def __post_init__(self):
        self.patterns = [
            re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE) for t in self.triggers
        ]


class ToolRouter:
    """
    Commercial ToolRouter API.
    Wraps the upstream deterministic hashing router with a decorator-based
    registration interface compatible with LangChain, SmolAgents, bare Python,
    and OpenAI-style JSON schema tool lists.

    Usage A – decorator:
        router = ToolRouter()
        @router.register(triggers=["weather", "forecast"])
        def get_weather(city): ...

    Usage B – JSON schema list (OpenAI / Anthropic format):
        router = ToolRouter([{"name": "...", "description": "...", "parameters": {...}}])
    """

    def __init__(self, tools: Optional[List[Dict]] = None):
        self._tools: Dict[str, ToolDefinition] = {}
        self._rules: List[Tuple[re.Pattern, str, float]] = []
        self._fallback_tools: List[str] = []
        if tools:
            for t in tools:
                spec = t.get("function", t) if isinstance(t.get("function"), dict) else t
                name = spec.get("name", "")
                desc = spec.get("description", "")
                tags = spec.get("tags", t.get("tags", []))
                params = []
                props = spec.get("parameters", {}).get("properties", {})
                required = spec.get("parameters", {}).get("required", [])
                for pname, pspec in props.items():
                    params.append({
                        "name": pname,
                        "type": pspec.get("type", "string"),
                        "required": pname in required,
                    })
                triggers = tags if tags else [
                    w for w in desc.lower().split() if len(w) > 3
                ][:5] or [name]
                self._tools[name] = ToolDefinition(
                    name=name,
                    func=lambda **kw: kw,
                    triggers=triggers,
                    description=desc,
                    params=params,
                    schema=t,
                )

    def add_rule(self, pattern: str, tool_name: str, boost: float = 10.0):
        """Add an explicit regex boost rule for a specific tool."""
        self._rules.append((re.compile(pattern, re.IGNORECASE), tool_name, boost))

    def set_fallback_tools(self, tool_names: List[str]):
        """Tools to return when no match meets min_score threshold."""
        self._fallback_tools = tool_names

    def register(
        self,
        name: Optional[str] = None,
        triggers: Optional[List[str]] = None,
        description: str = "",
        params: Optional[List[Dict]] = None,
    ):
        """Decorator to register a Python function as a routable tool."""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            tool_triggers = triggers or [tool_name.replace("_", " ")]
            self._tools[tool_name] = ToolDefinition(
                name=tool_name,
                func=func,
                triggers=tool_triggers,
                description=description or (func.__doc__ or ""),
                params=params or [],
            )
            return func
        return decorator

    def _build_inline_model(self) -> Dict:
        """Build a lightweight inline model dict for the upstream hashing router."""
        idf: Dict[int, float] = {}
        centroids: Dict[str, Dict[int, float]] = {}
        tools_meta = []
        for name, tool in self._tools.items():
            param_names = " ".join(p.get("name", "") for p in tool.params)
            combined = " ".join([
                name.replace("_", " "),
                " ".join(tool.triggers),
                tool.description,
                param_names,
            ])
            vec = embed(combined, _DIM, idf)
            centroids[name] = vec
            tools_meta.append({"name": name, "params": tool.params})
        return {"dim": _DIM, "idf": idf, "centroids": centroids, "tools": tools_meta}

    def route(self, query: str, top_k: int = 1, min_score: float = 0.0) -> RouteResult:
        """
        Route a query deterministically. Returns RouteResult with
        selected_tools, scores, confidence, and estimated token_savings_pct.
        """
        t0 = time.perf_counter()
        if not self._tools:
            return RouteResult(
                query=query, selected_tools=list(self._fallback_tools),
                scores={}, confidence=0.0, token_savings_pct=0.0,
            )
        model = self._build_inline_model()
        raw = _upstream_route(query, model, top_k=len(self._tools))
        # Scale upstream cosine similarity [0..1] to [0..100] to align with commercial thresholds
        scores: Dict[str, float] = {k: v * 100.0 for k, v in raw["scores"].items()}
        explanation: Dict[str, List[str]] = {name: [] for name in self._tools}

        # Deterministic entity & syntax alignment boosts
        has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", query))
        has_sql = bool(re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE)\b", query, re.IGNORECASE))

        for name, tool in self._tools.items():
            param_names = {p.get("name", "").lower() for p in tool.params}
            trigger_set = {t.lower() for t in tool.triggers}
            if has_email and ("email" in param_names or "email" in trigger_set or "email" in name.lower()):
                scores[name] += 25.0
                explanation[name].append("matched entity: email")
            if has_sql and ("sql" in param_names or "sql" in trigger_set or "database" in trigger_set or "sql" in name.lower()):
                scores[name] += 25.0
                explanation[name].append("matched syntax: sql")

        # Apply explicit regex boost rules
        for pattern, tool_name, boost in self._rules:
            if pattern.search(query) and tool_name in scores:
                scores[tool_name] = scores[tool_name] + boost
                explanation[tool_name].append(f"matched rule: {pattern.pattern}")

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        selected = [name for name, score in ranked[:top_k] if score >= min_score]
        if not selected:
            selected = list(self._fallback_tools)

        total = len(self._tools)
        savings_pct = round(((total - len(selected)) / total) * 100, 1) if total > 0 else 0.0
        confidence = ranked[0][1] if ranked else 0.0

        # Estimate token counts (~1 token per 4 chars of schema JSON, fallback ~120 tokens/tool)
        orig_tokens = sum(max(120, len(json.dumps(t.schema)) // 4) if t.schema else 120 for t in self._tools.values())
        routed_tokens = sum(
            max(120, len(json.dumps(self._tools[n].schema)) // 4) if (n in self._tools and self._tools[n].schema) else 120
            for n in selected
        )
        latency_us = round((time.perf_counter() - t0) * 1_000_000, 2)

        return RouteResult(
            query=query,
            selected_tools=selected,
            scores=scores,
            confidence=round(confidence, 4),
            token_savings_pct=savings_pct,
            explanation=explanation,
            latency_microseconds=latency_us,
            all_evaluated_count=total,
            selected_count=len(selected),
            estimated_prompt_tokens_original=orig_tokens,
            estimated_prompt_tokens_routed=routed_tokens,
        )

    def match(self, query: str) -> List[Tuple[str, float]]:
        """Return ranked (tool_name, score) list for a query."""
        result = self.route(query, top_k=len(self._tools))
        return sorted(result.scores.items(), key=lambda x: x[1], reverse=True)

    def prune_tools(self, query: str, top_k: int = 1, min_score: float = 0.0) -> List[Dict]:
        """Return only the top-k tool schemas relevant to the query (payload pruning)."""
        result = self.route(query, top_k=top_k, min_score=min_score)
        return [
            self._tools[name].schema
            for name in result.selected_tools
            if name in self._tools and self._tools[name].schema
        ]

    def dispatch(self, query: str, **kwargs) -> Any:
        """Route query and invoke the matched tool function."""
        result = self.route(query, top_k=1)
        if not result.selected_tools:
            raise LookupError(f"No deterministic tool matched: '{query}'")
        best_name = result.selected_tools[0]
        return self._tools[best_name].func(**kwargs)


# Default module-level singleton
default_router = ToolRouter()
tool = default_router.register
route = default_router.dispatch
