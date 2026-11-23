"""
Deterministic multi-factor matcher combining regex rules, entity heuristics,
negation detection, and schema constraint alignment.
"""

import re
from typing import Dict, List, Set, Tuple, Optional, Pattern, Any
from .schema import ToolDefinition, tokenize_identifier

# Precompiled universal entity recognizers for parameter constraint matching
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
URL_REGEX = re.compile(r"https?://[^\s/$.?#].[^\s]*")
UUID_REGEX = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
SQL_REGEX = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|FROM|WHERE)\b", re.IGNORECASE)
DATE_REGEX = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|today|yesterday|tomorrow)\b", re.IGNORECASE)

# Negation detection to avoid false-positive tool calls
NEGATION_REGEX = re.compile(r"\b(do\s+not|don't|dont|never|without|exclude|avoid|skip)\s+([a-zA-Z0-9_]+(?:\s+[a-zA-Z0-9_]+)?)", re.IGNORECASE)

class DeterministicMatcher:
    """Multi-stage deterministic scoring engine with pre-indexed parameter lookups."""
    __slots__ = ("tools", "regex_rules", "synonyms", "entity_param_index")

    def __init__(self, tools: Dict[str, ToolDefinition]):
        self.tools = tools
        self.regex_rules: List[Tuple[Pattern, str, float]] = [] # (pattern, tool_name, boost)
        self.synonyms: Dict[str, Set[str]] = {
            "fetch": {"get", "retrieve", "read", "find", "load"},
            "lookup": {"search", "find", "query", "check"},
            "create": {"new", "insert", "add", "post", "make"},
            "modify": {"update", "edit", "change", "patch"},
            "delete": {"remove", "destroy", "drop", "cancel"},
            "calculate": {"compute", "math", "sum", "eval"},
            "execute": {"run", "call", "trigger", "invoke"},
            "send": {"deliver", "mail", "notify", "push", "post"},
            "browse": {"crawl", "scrape", "visit", "url", "http", "web"}
        }
        self.entity_param_index: Dict[str, Set[str]] = {}
        self._build_param_indices()

    def _build_param_indices(self) -> None:
        """Pre-index entity parameter and tag mappings for sub-millisecond O(1) matching."""
        self.entity_param_index.clear()
        for tool_name, tool_def in self.tools.items():
            # Index name tokens and tags with higher boost (5.0)
            for tok in (tool_def.name_tokens | tool_def.tags):
                if tok not in self.entity_param_index:
                    self.entity_param_index[tok] = {}
                self.entity_param_index[tok][tool_name] = 5.0

            for p_name, p_obj in tool_def.parameters.items():
                p_lower = p_name.lower()
                if p_lower not in self.entity_param_index:
                    self.entity_param_index[p_lower] = {}
                self.entity_param_index[p_lower][tool_name] = max(self.entity_param_index[p_lower].get(tool_name, 0.0), 3.0)
                for tok in p_obj.tokens:
                    if tok not in self.entity_param_index:
                        self.entity_param_index[tok] = {}
                    self.entity_param_index[tok][tool_name] = max(self.entity_param_index[tok].get(tool_name, 0.0), 2.5)

    def reindex(self) -> None:
        self._build_param_indices()

    def add_rule(self, pattern: str, target_tool: str, boost: float = 10.0) -> None:
        """Register explicit deterministic routing rule."""
        self.regex_rules.append((re.compile(pattern, re.IGNORECASE), target_tool, boost))

    def detect_entities(self, query: str) -> Set[str]:
        """Detect entity types in query to match against tool parameter schemas."""
        entities = set()
        if EMAIL_REGEX.search(query):
            entities.add("email")
            entities.add("recipient")
        if URL_REGEX.search(query):
            entities.add("url")
            entities.add("link")
            entities.add("uri")
        if UUID_REGEX.search(query):
            entities.add("id")
            entities.add("uuid")
        if SQL_REGEX.search(query):
            entities.add("sql")
            entities.add("query")
        if DATE_REGEX.search(query):
            entities.add("date")
            entities.add("time")
            entities.add("timestamp")
        return entities

    def detect_negations(self, query: str) -> Set[str]:
        """Identify action words that user explicitly requested to NOT execute."""
        suppressed_terms = set()
        for match in NEGATION_REGEX.finditer(query):
            phrase = match.group(2).lower()
            tokens = tokenize_identifier(phrase)
            suppressed_terms.update(tokens)
        return suppressed_terms

    def match(self, query: str, base_scores: Dict[str, float]) -> Tuple[Dict[str, float], Dict[str, List[str]]]:
        """
        Refine base token scores using deterministic rules, parameter alignment,
        and negation penalties. Sub-millisecond indexed lookup.
        """
        scores = dict(base_scores)
        explanations: Dict[str, List[str]] = {}

        query_lower = query.lower()
        entities = self.detect_entities(query)
        negations = self.detect_negations(query)

        # 1. Custom Regex Rule Boosting
        for pattern, tool_name, boost in self.regex_rules:
            if tool_name in self.tools and pattern.search(query):
                scores[tool_name] = scores.get(tool_name, 0.0) + boost
                explanations.setdefault(tool_name, []).append(f"matched rule: {pattern.pattern} (+{boost})")

        # 2. Entity Parameter & Name Alignment (O(1) indexed lookup)
        for entity in entities:
            matching_tool_weights = self.entity_param_index.get(entity)
            if matching_tool_weights:
                for tool_name, weight in matching_tool_weights.items():
                    scores[tool_name] = scores.get(tool_name, 0.0) + weight
                    explanations.setdefault(tool_name, []).append(f"entity match on {entity} (+{weight})")

        # 3. Exact Name Match Bonus on candidates already hit by token index
        for tool_name in base_scores:
            if tool_name.lower() in query_lower:
                scores[tool_name] = scores.get(tool_name, 0.0) + 12.0
                explanations.setdefault(tool_name, []).append("exact tool name in query (+12.0)")

        # 4. Negation Penalty on candidate tools
        if negations:
            for tool_name in scores:
                tool_def = self.tools.get(tool_name)
                if not tool_def:
                    continue
                # If tool has 'preview', 'dry_run', 'read', 'get' and query has preview, don't penalize
                is_safe_preview = any(tok in tool_def.name_tokens for tok in ("preview", "dry_run", "read", "view"))
                for neg_tok in negations:
                    if is_safe_preview and neg_tok not in ("preview", "dry_run", "read", "view"):
                        continue
                    if neg_tok in tool_def.name_tokens or neg_tok in tool_def.tags:
                        penalty = -15.0
                        scores[tool_name] += penalty
                        explanations.setdefault(tool_name, []).append(f"negation penalty on '{neg_tok}' ({penalty})")

        return scores, explanations
