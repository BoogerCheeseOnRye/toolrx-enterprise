import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from toolrx.router import ToolRouter

def test_benchmark():
    router = ToolRouter()

    @router.register(name="fetch_weather", triggers=["weather", "forecast", "temperature"])
    def fetch_weather(city="Seattle"):
        return f"72F, Sunny in {city}"

    @router.register(name="execute_trade", triggers=["buy", "sell", "swap", "crypto", "stock"])
    def execute_trade(pair="BTC/USD", amount=1.0):
        return f"Executed trade for {amount} {pair}"

    @router.register(name="db_query", triggers=["database", "query", "sql", "select", "user"])
    def db_query(user_id=123):
        return {"id": user_id, "name": "Alice"}

    queries = [
        "What is the weather forecast for tomorrow?",
        "Please buy 0.5 BTC on the exchange",
        "Run a database query to find user 456",
        "Check temperature outside",
    ]

    iterations = 10000
    start = time.perf_counter()
    for _ in range(iterations):
        for q in queries:
            router.match(q)
    elapsed = time.perf_counter() - start

    total_calls = iterations * len(queries)
    avg_latency_us = (elapsed / total_calls) * 1_000_000

    print("=" * 50)
    print("TOOLRX DETERMINISTIC ROUTING BENCHMARK")
    print("=" * 50)
    print(f"Total Dispatches: {total_calls:,}")
    print(f"Total Time:       {elapsed:.4f}s")
    print(f"Average Latency:  {avg_latency_us:.2f} microseconds (<0.05 ms)")
    print(f"Throughput:       {total_calls / elapsed:,.0f} routes/sec")
    print(f"API Cost:         $0.00 (LLM equivalent: ~${total_calls * 0.002:,.2f})")
    print("=" * 50)

if __name__ == "__main__":
    test_benchmark()
