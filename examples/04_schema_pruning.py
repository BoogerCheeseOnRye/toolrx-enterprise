"""
Example 4: 500-Tool Microsecond Schema Pruning Demo
Demonstrates scaling up to 500 enterprise API schemas with sub-millisecond selection.
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from toolrx import ToolRouter
from benchmarks.datasets import generate_tool_catalog

def main():
    print("Generating 500 enterprise tool schemas...")
    tools_500 = generate_tool_catalog(500)
    print(f"Catalog generated: {len(tools_500)} tools")

    router = ToolRouter(tools_500)

    query = "SELECT count(*) FROM user_orders WHERE created_at > '2026-01-01';"
    print(f"\nUser Query: {query}")

    t0 = time.perf_counter_ns()
    res = router.route(query, top_k=3)
    t1 = time.perf_counter_ns()

    print(f"Routing Complete in {(t1 - t0) / 1000.0:.2f} μs ({(t1 - t0) / 1_000_000.0:.3f} ms)")
    print(f"Selected Tools: {res.selected_tools}")
    print(f"Original Catalog Tokens: {res.estimated_prompt_tokens_original:,} tokens")
    print(f"Routed Prompt Tokens:   {res.estimated_prompt_tokens_routed:,} tokens")
    print(f"Token Reduction:        {res.token_savings_pct}%")
    print(f"Total Tokens Saved:     {res.tokens_saved:,} tokens in a single request!")

if __name__ == "__main__":
    main()
