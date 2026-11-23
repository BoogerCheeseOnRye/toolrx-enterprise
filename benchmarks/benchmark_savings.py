"""
Token savings, cost reduction, and precision benchmark for ToolRx.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from toolrx.router import ToolRouter
from benchmarks.datasets import generate_tool_catalog, BENCHMARK_QUERIES

def run_savings_benchmark(tool_counts=(50, 100, 500)):
    results = {}

    for count in tool_counts:
        tools = generate_tool_catalog(count)
        router = ToolRouter(tools)

        total_original_tokens = 0
        total_routed_tokens = 0
        hits = 0

        for item in BENCHMARK_QUERIES:
            res = router.route(item["query"], top_k=3)
            total_original_tokens += res.estimated_prompt_tokens_original
            total_routed_tokens += res.estimated_prompt_tokens_routed

            # Check recall@3
            expected = item["expected_tool"]
            if any(expected in tool_name for tool_name in res.selected_tools):
                hits += 1

        tokens_saved = total_original_tokens - total_routed_tokens
        savings_pct = (tokens_saved / total_original_tokens) * 100.0 if total_original_tokens else 0.0
        accuracy = (hits / len(BENCHMARK_QUERIES)) * 100.0

        # Model pricing reference: GPT-4o input tokens = $2.50 / 1M tokens
        # 1M agent calls savings
        cost_saved_per_1m_calls = (tokens_saved / len(BENCHMARK_QUERIES)) * (2.50 / 1_000_000.0) * 1_000_000.0

        results[count] = {
            "catalog_size": count,
            "original_tokens_per_call": total_original_tokens // len(BENCHMARK_QUERIES),
            "routed_tokens_per_call": total_routed_tokens // len(BENCHMARK_QUERIES),
            "tokens_saved_per_call": tokens_saved // len(BENCHMARK_QUERIES),
            "token_reduction_pct": round(savings_pct, 1),
            "top3_recall_pct": round(accuracy, 1),
            "usd_saved_per_1m_calls": round(cost_saved_per_1m_calls, 2),
        }

    return results

if __name__ == "__main__":
    res = run_savings_benchmark()
    print("Savings Benchmark Results:")
    for size, metrics in res.items():
        print(f"[{size} tools] Original={metrics['original_tokens_per_call']} toks -> Routed={metrics['routed_tokens_per_call']} toks | Savings={metrics['token_reduction_pct']}% | Top-3 Recall={metrics['top3_recall_pct']}% | Saved/1M calls=${metrics['usd_saved_per_1m_calls']}")
