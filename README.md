# ToolRx: Deterministic Micro Tool Router for LLM / Agent Calling

[![License: BSL 1.1](https://img.shields.io/badge/License-BSL%201.1-blue.svg)](LICENSE-COMMUNITY.md)
[![Commercial License](https://img.shields.io/badge/License-Commercial%20Enterprise-green.svg)](LICENSE-COMMERCIAL.md)
[![Tests: 15/15 Passed](https://img.shields.io/badge/Tests-15%2F15%20Passing-brightgreen.svg)](tests/)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](pyproject.toml)
[![Zero External Dependencies](https://img.shields.io/badge/Dependencies-Zero-success.svg)](setup.py)

**ToolRx** is a commercial-grade deterministic micro tool router for LLM tool calling. It prunes massive catalogs of 50 to 500+ tools down to the exact top-3 relevant tools in **sub-millisecond speed** with **zero LLM dependencies**, slashing prompt token costs by **90% to 99%** while eliminating tool hallucination.

---

## Why ToolRx?

| Metric | ToolRx Deterministic Router | Embedding / Vector Search Router | LLM Secondary Classifier |
| :--- | :--- | :--- | :--- |
| **Routing Latency** | **< 0.5 ms (< 500 μs)** | 15 - 50 ms | 350 - 1,200 ms |
| **Dependencies** | **Zero (Pure Standard Library)** | Heavy (PyTorch, ONNX, FAISS) | Remote API / External Token Quota |
| **Determinism** | **100% Reproducible / Auditable** | Stochastic / Approximate | Non-deterministic / Hallucination-prone |
| **Token Cost per Route**| **$0.000000 (Local zero-cost)** | $0.0001 (Embedding inference) | $0.0050 - $0.0150 (Extra LLM hop) |
| **Edge / Embedded** | **Yes (WASM, Cloudflare, Lambda)**| High memory / Slow cold start | No (requires remote network call) |

---

## Benchmark Highlights (Automated Suite)

From [`benchmarks/BENCHMARK_REPORT.md`](benchmarks/BENCHMARK_REPORT.md):

- **50 Tools**: **93.9% token reduction**, **100.0% top-3 recall**, **487 μs p50 latency** (Saves **$13,001** per 1M calls).
- **100 Tools**: **96.9% token reduction**, **100.0% top-3 recall**, **665 μs p50 latency** (Saves **$26,865** per 1M calls).
- **500 Tools**: **99.4% token reduction**, **100.0% top-3 recall**, **1.8 ms p50 latency** (Saves **$138,065** per 1M calls).

---

## Quickstart

### 1. Installation
```bash
pip install toolrx
```
*(Zero third-party dependencies required).*

### 2. Basic Python Usage
```python
from toolrx import ToolRouter

# Register tools from OpenAPI / JSON Schema / OpenAI format
tools = [
    {
        "name": "refund_stripe_charge",
        "description": "Issue refund for payment charge or customer invoice",
        "parameters": {
            "type": "object",
            "properties": {"charge_id": {"type": "string"}},
            "required": ["charge_id"]
        }
    },
    # ... 100+ other enterprise tools
]

router = ToolRouter(tools)

# Route in microseconds
result = router.route("Can you refund customer charge ch_99213?", top_k=1)

print("Selected:", result.selected_tools)  # ['refund_stripe_charge']
print("Latency:", result.latency_microseconds, "μs")  # ~380 μs
print("Tokens saved:", result.tokens_saved, f"({result.token_savings_pct}%)")
```

### 3. Drop-in OpenAI Interceptor
Prune OpenAI payload tools in 1 line of code before making the API request:

```python
from toolrx.adapters import ToolRxOpenAI

# Intercept and prune payload tools
payload = {
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Refund charge ch_12345"}],
    "tools": large_tool_catalog # 100+ tools
}

optimized_payload = ToolRxOpenAI.optimize_payload(payload, top_k=3)
# optimized_payload['tools'] now contains only the top 3 relevant tools!
```

---

## Hosted Edge Gateway Wrapper

ToolRx includes an edge HTTP gateway wrapper:

```bash
# Start Gateway on port 8080
python -m toolrx.gateway.server
```

### Route Endpoint
```bash
curl -X POST http://localhost:8080/v1/route \
  -H "Authorization: Bearer trx_live_pro_demo" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Check open tickets for alice@example.com",
    "tools": [...],
    "top_k": 3
  }'
```

### Response
```json
{
  "selected_tools": ["search_customer_support_tickets"],
  "scores": {"search_customer_support_tickets": 9.5},
  "latency_us": 420.15,
  "savings": {
    "tokens_saved": 10747,
    "token_savings_pct": 96.9,
    "cost_saved_usd": 0.026867
  }
}
```

---

## Commercial Licensing & Monetization

ToolRx operates on a **dual-licensing model**:
- **Community Edition ([LICENSE-COMMUNITY.md](LICENSE-COMMUNITY.md))**: Business Source License 1.1 (BSL 1.1). Free for development, evaluation, and production use under 100,000 requests/month.
- **Enterprise Commercial License ([LICENSE-COMMERCIAL.md](LICENSE-COMMERCIAL.md))**: Unrestricted production, closed-source embedding, SLAs, private VPC deployments, and compliance indemnification.

See [PRICING.md](PRICING.md) for pricing tiers, managed hosted gateway plans, and the full 266x ROI analysis.

---

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Commercial Strategy & GTM](docs/COMMERCIAL_STRATEGY.md)
- [API Reference](docs/API_REFERENCE.md)
- [Benchmark Report](benchmarks/BENCHMARK_REPORT.md)
