"""
Latency micro-benchmarks for ToolRx.
Measures p50, p95, p99 routing latency across varying catalog sizes (50, 100, 500 tools).
"""

import time
import sys
import os

# Add parent path to allow importing toolrx
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from toolrx.router import ToolRouter
from benchmarks.datasets import generate_tool_catalog, BENCHMARK_QUERIES

def run_latency_benchmark(tool_counts=(50, 100, 500), iterations_per_query=100):
    """
    Benchmark deterministic routing latency in microseconds.
    """
    results = {}

    for count in tool_counts:
        tools = generate_tool_catalog(count)
        router = ToolRouter(tools)

        # Warmup
        for item in BENCHMARK_QUERIES:
            router.route(item["query"], top_k=3)

        latencies_us = []
        for _ in range(iterations_per_query):
            for item in BENCHMARK_QUERIES:
                t0 = time.perf_counter_ns()
                router.route(item["query"], top_k=3)
                t1 = time.perf_counter_ns()
                latencies_us.append((t1 - t0) / 1000.0)

        latencies_us.sort()
        n = len(latencies_us)
        results[count] = {
            "catalog_size": count,
            "total_calls": n,
            "p50_us": round(latencies_us[int(n * 0.50)], 2),
            "p95_us": round(latencies_us[int(n * 0.95)], 2),
            "p99_us": round(latencies_us[int(n * 0.99)], 2),
            "min_us": round(latencies_us[0], 2),
            "max_us": round(latencies_us[-1], 2),
            "avg_us": round(sum(latencies_us) / n, 2),
        }

    return results

if __name__ == "__main__":
    res = run_latency_benchmark()
    print("Latency Benchmark Results (Microseconds):")
    for size, metrics in res.items():
        print(f"[{size} tools] avg={metrics['avg_us']}μs | p50={metrics['p50_us']}μs | p95={metrics['p95_us']}μs | p99={metrics['p99_us']}μs")
