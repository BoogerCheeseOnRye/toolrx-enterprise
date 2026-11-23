"""
High-performance prefix trie and token indexing for sub-microsecond token matching.
Zero external dependencies.
"""

from typing import Dict, List, Set, Any, Optional

class TrieNode:
    __slots__ = ("children", "tool_names", "is_end")

    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.tool_names: Set[str] = set()
        self.is_end: bool = False

class PrefixTrie:
    """Trie structure storing word prefixes mapped to matching tools."""
    __slots__ = ("root",)

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, tool_name: str) -> None:
        if not word:
            return
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.tool_names.add(tool_name)
        node.is_end = True

    def find_prefix(self, prefix: str) -> Set[str]:
        """Return all tools that match the given prefix."""
        if not prefix:
            return set()
        node = self.root
        for char in prefix:
            if char not in node.children:
                return set()
            node = node.children[char]
        return node.tool_names

    def find_exact(self, word: str) -> Set[str]:
        """Return tools associated directly with this exact token."""
        if not word:
            return set()
        node = self.root
        for char in word:
            if char not in node.children:
                return set()
            node = node.children[char]
        if node.is_end:
            return node.tool_names
        return set()

SYNONYM_MAP = {
    "lookup": "search",
    "look": "search",
    "find": "search",
    "query": "search",
    "fetch": "get",
    "retrieve": "get",
    "obtain": "get",
    "modify": "update",
    "change": "update",
    "remove": "delete",
    "cancel": "delete",
    "sql": "query",
    "reboot": "restart",
}

def stem_token(word: str) -> str:
    """Fast, zero-dependency Porter-like suffix stripper."""
    if len(word) > 4:
        if word.endswith("ies"):
            return word[:-3] + "y"
        if word.endswith("es"):
            return word[:-2]
        if word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
        if word.endswith("ing") and len(word) > 5:
            return word[:-3]
        if word.endswith("ed") and len(word) > 5:
            return word[:-2]
    return word

class TokenIndex:
    """Inverted index mapping tokens to tools with positional and field weighting."""
    __slots__ = ("token_map", "trie", "total_tools")

    def __init__(self):
        self.token_map: Dict[str, Dict[str, float]] = {}  # token -> {tool_name: weight}
        self.trie = PrefixTrie()
        self.total_tools = 0

    def add_tool_tokens(self, tool_name: str, name_tokens: Set[str], desc_tokens: Set[str], param_tokens: Set[str], tags: Set[str]) -> None:
        self.total_tools += 1
        token_weights: Dict[str, float] = {}

        def record(tok: str, weight: float):
            token_weights[tok] = max(token_weights.get(tok, 0.0), weight)
            stem = stem_token(tok)
            if stem != tok:
                token_weights[stem] = max(token_weights.get(stem, 0.0), weight * 0.9)
            self.trie.insert(tok, tool_name)
            if stem != tok:
                self.trie.insert(stem, tool_name)

        for tok in name_tokens:
            record(tok, 5.0)

        for tok in tags:
            record(tok, 4.0)

        for tok in param_tokens:
            record(tok, 2.5)

        for tok in desc_tokens:
            record(tok, 1.0)

        for tok, weight in token_weights.items():
            if tok not in self.token_map:
                self.token_map[tok] = {}
            self.token_map[tok][tool_name] = weight

    def query_tokens(self, tokens: List[str], allow_prefix: bool = True) -> Dict[str, float]:
        """Score tools based on token hits in sub-microseconds."""
        tool_scores: Dict[str, float] = {}

        for tok in tokens:
            candidates = [tok]
            stem = stem_token(tok)
            if stem != tok:
                candidates.append(stem)
            syn = SYNONYM_MAP.get(tok) or SYNONYM_MAP.get(stem)
            if syn and syn not in candidates:
                candidates.append(syn)

            for cand in candidates:
                if cand in self.token_map:
                    for tool_name, weight in self.token_map[cand].items():
                        tool_scores[tool_name] = tool_scores.get(tool_name, 0.0) + weight

            if allow_prefix and len(tok) >= 4:
                prefix_tools = self.trie.find_prefix(tok[:4])
                for tool_name in prefix_tools:
                    tool_scores[tool_name] = tool_scores.get(tool_name, 0.0) + 0.8

        return tool_scores
