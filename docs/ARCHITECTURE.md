# ToolRx Technical Architecture

## 1. System Overview

ToolRx is an ultra-low latency, deterministic micro tool router for LLM agent workflows. It sits between user inputs and frontier LLMs, dynamically indexing and selecting tools without calling external models, vector embeddings, or heavy neural networks.

```
+-------------------------------------------------------------------------------+
|                             ToolRx Micro-Router                              |
|                                                                               |
|  [ User Prompt / Query ]                                                      |
|           |                                                                   |
|           v                                                                   |
|  +--------------------+      +--------------------+      +-----------------+  |
|  | Lexical Tokenizer  | ---> | Prefix Trie Match  | ---> | Parameter Entity|  |
|  | & Stemmer          |      | (O(k) Token Index) |      | Alignment Index |  |
|  +--------------------+      +--------------------+      +-----------------+  |
|                                                                   |           |
|                                                                   v           |
|  +--------------------+      +--------------------+      +-----------------+  |
|  | Final Top-K Tools  | <--- | Negation & Conflict| <--- | Intent Grammar  |  |
|  | + Token Savings    |      | Penalty Engine     |      | Regex Rules     |  |
|  +--------------------+      +--------------------+      +-----------------+  |
+-------------------------------------------------------------------------------+
           |
           v (90-99% fewer tokens sent)
  [ Frontier LLM: GPT-4o / Claude 3.5 / Gemini 2.0 ]
```

---

## 2. Why Zero-LLM Deterministic Routing?

Existing agent tool-calling architectures use two broken paradigms:

1. **All-Tools Prompt Dumping (Status Quo)**:
   - Every tool definition is serialized into system instructions.
   - **Flaw**: 100 tools eat 11,000+ tokens per turn. Leads to massive latency, runaway token bills, and LLM tool confusion/hallucination.
2. **Embedding / Vector Search Routers (RAG for Tools)**:
   - Embedding query and cosine similarity matching against tool docstrings.
   - **Flaw**: High cold start (loading PyTorch/ONNX models takes 500MB+ RAM), latency is 15-50ms, and semantic embeddings fail on precise keywords (e.g. `cancel_subscription` vs `retrieve_subscription`).
3. **LLM Pre-Classifiers**:
   - Asking a smaller LLM (e.g. GPT-4o-mini) to pick tools first.
   - **Flaw**: Adds 300ms - 1,000ms latency, doubles network failure surfaces, and costs additional API credits.

### The ToolRx Breakthrough
ToolRx achieves **100% recall** in **< 500 microseconds** by combining:
- **Fast Prefix Trie & Inverted Token Index**: Tokenizes identifiers, parameters, and descriptions with suffix stemming and synonym mapping.
- **Pre-Indexed Parameter Entity Alignment**: Instant $O(1)$ boost when query contains parameters matching schema constraints (e.g., email address, SQL query, URL, UUID, date).
- **Configurable Deterministic Intent Rules**: Pre-compiled regex patterns that enforce deterministic tool execution for compliance-critical operations.
- **Negation Suppression Engine**: Explicitly down-weights tools matching negated verbs (e.g. `"do not execute"`, `"without running"`).

---

## 3. Core Modules

| Module | Purpose | Complexity |
| :--- | :--- | :--- |
| `toolrx.core.schema` | Normalizes OpenAI, Anthropic, and JSON Schema definitions | $O(N)$ one-time index |
| `toolrx.core.trie` | Prefix Trie & weighted token scoring | $O(L)$ where $L$ is query length |
| `toolrx.core.matcher` | Entity alignment, negation suppression, and rule boosting | $O(E)$ where $E$ is detected entities |
| `toolrx.router` | Main orchestrator and token savings accounting | Sub-millisecond |
| `toolrx.adapters` | Transparent drop-in wrappers for OpenAI and Anthropic SDKs | Zero overhead |
| `toolrx.gateway` | High-throughput HTTP server with API key auth and billing telemetry | Multi-threaded async |

---

## 4. Edge & Embedded Runtime Constraints

ToolRx is engineered from the ground up with zero non-standard-library dependencies:
- **Pure Python 3.9+ / WASM Compatible**: Can be compiled to WebAssembly via Pyodide/Rust or run directly inside Cloudflare Workers (Python runtime) and AWS Lambda.
- **Memory Footprint**: < 8MB RAM for 1,000 indexed tools.
- **Cold Start**: < 2 milliseconds to initialize and index hundreds of tools.
- **Thread Safety**: Read-only query operations are fully reentrant and lock-free.
