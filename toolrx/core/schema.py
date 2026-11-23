"""
Schema definitions and normalization for toolrx.
Provides zero-dependency representations of tools, schemas, and routing results.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
import re

TOKEN_SPLIT_REGEX = re.compile(r"[^a-zA-Z0-9]+")
CAMEL_CASE_REGEX = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")

def tokenize_identifier(text: str) -> List[str]:
    """Split snake_case, camelCase, kebab-case into normalized lower-case tokens."""
    if not text:
        return []
    # Expand camelCase
    expanded = CAMEL_CASE_REGEX.sub(" ", text)
    # Split by non-alphanumeric
    parts = TOKEN_SPLIT_REGEX.split(expanded.lower())
    return [p for p in parts if p and len(p) > 1]

@dataclass(slots=True)
class ToolParameter:
    name: str
    type: str = "string"
    description: str = ""
    required: bool = False
    tokens: Set[str] = field(default_factory=set)

    def __post_init__(self):
        if not self.tokens:
            toks = set(tokenize_identifier(self.name))
            if self.description:
                toks.update(tokenize_identifier(self.description))
            self.tokens = toks

@dataclass(slots=True)
class ToolDefinition:
    name: str
    description: str = ""
    parameters: Dict[str, ToolParameter] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    raw_schema: Dict[str, Any] = field(default_factory=dict)
    name_tokens: Set[str] = field(default_factory=set)
    desc_tokens: Set[str] = field(default_factory=set)
    all_tokens: Set[str] = field(default_factory=set)
    estimated_tokens: int = 0

    def __post_init__(self):
        if not self.name_tokens:
            self.name_tokens = set(tokenize_identifier(self.name))
        if not self.desc_tokens:
            self.desc_tokens = set(tokenize_identifier(self.description))
        if not self.all_tokens:
            self.all_tokens = set(self.name_tokens) | set(self.desc_tokens) | set(self.tags)
            for param in self.parameters.values():
                self.all_tokens.update(param.tokens)
        if not self.estimated_tokens:
            # Conservative rule of thumb: ~4 characters per token in raw json/text
            schema_len = len(str(self.raw_schema)) if self.raw_schema else len(self.name) * 2 + len(self.description)
            self.estimated_tokens = max(15, schema_len // 4)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolDefinition":
        """
        Normalize OpenAI, Anthropic, or JSON Schema tool formats:
        - OpenAI: {"type": "function", "function": {"name": "...", "description": "...", "parameters": {...}}}
        - Anthropic: {"name": "...", "description": "...", "input_schema": {...}}
        - Standard: {"name": "...", "description": "...", "parameters": {...}}
        """
        raw = data
        if "function" in data and isinstance(data["function"], dict):
            fn = data["function"]
            name = fn.get("name", "")
            description = fn.get("description", "")
            param_spec = fn.get("parameters", {})
        else:
            name = data.get("name", "")
            description = data.get("description", "")
            param_spec = data.get("parameters") or data.get("input_schema") or {}

        parameters: Dict[str, ToolParameter] = {}
        if isinstance(param_spec, dict):
            props = param_spec.get("properties", {})
            required_set = set(param_spec.get("required", []))
            for p_name, p_def in props.items():
                if isinstance(p_def, dict):
                    parameters[p_name] = ToolParameter(
                        name=p_name,
                        type=p_def.get("type", "string"),
                        description=p_def.get("description", ""),
                        required=(p_name in required_set)
                    )

        tags = set(data.get("tags", []))
        return cls(
            name=name,
            description=description,
            parameters=parameters,
            tags=tags,
            raw_schema=raw
        )

@dataclass(slots=True)
class RouteResult:
    query: str
    selected_tools: List[str]
    scores: Dict[str, float]
    all_evaluated_count: int
    selected_count: int
    latency_microseconds: float
    estimated_prompt_tokens_original: int
    estimated_prompt_tokens_routed: int
    tokens_saved: int
    token_savings_pct: float
    explanation: Dict[str, List[str]] = field(default_factory=dict)
