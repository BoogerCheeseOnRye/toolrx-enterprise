# ToolRx API Reference & Documentation

## Python SDK Reference

### `ToolRouter(tools=None)`
Primary router class. Zero external dependencies.

```python
from toolrx import ToolRouter

router = ToolRouter(tools=tool_list)
```

#### Methods:
- **`register_tool(tool: Union[Dict, ToolDefinition]) -> ToolDefinition`**:
  Registers an individual tool. Accepts standard JSON Schema, OpenAI function format, or Anthropic tool format.
- **`register_tools(tools: List[Union[Dict, ToolDefinition]]) -> None`**:
  Batch registers a list of tools.
- **`add_rule(pattern: str, target_tool: str, boost: float = 10.0) -> None`**:
  Adds an explicit regex rule that guarantees deterministic boosting when pattern matches user query.
- **`set_fallback_tools(tool_names: List[str]) -> None`**:
  Specifies fallback tools to return if no tools exceed the minimum relevance threshold.
- **`route(query: str, top_k: int = 3, min_score: float = 1.0) -> RouteResult`**:
  Executes sub-millisecond routing over indexed tools and returns `RouteResult`.
- **`prune_tools(query: str, top_k: int = 5, min_score: float = 1.0) -> List[Dict]`**:
  Returns the original raw tool dictionaries filtered down to the top-k tools.

---

### `RouteResult` Dataclass
- **`query`** (`str`): The routed user input.
- **`selected_tools`** (`List[str]`): List of top-k selected tool names.
- **`scores`** (`Dict[str, float]`): Match scores for selected tools.
- **`latency_microseconds`** (`float`): Precise execution time in microseconds.
- **`estimated_prompt_tokens_original`** (`int`): Token weight of entire tool catalog.
- **`estimated_prompt_tokens_routed`** (`int`): Token weight of selected tools.
- **`tokens_saved`** (`int`): Estimated prompt tokens saved.
- **`token_savings_pct`** (`float`): Percentage reduction in prompt tokens.
- **`explanation`** (`Dict[str, List[str]]`): Audit trail of rule matches and parameter hits.

---

### SDK Adapters

#### `ToolRxOpenAI`
```python
from toolrx.adapters import ToolRxOpenAI

# Intercept and optimize OpenAI payload dictionary
optimized_payload = ToolRxOpenAI.optimize_payload(payload, top_k=5)
```

#### `ToolRxAnthropic`
```python
from toolrx.adapters import ToolRxAnthropic

# Intercept and optimize Anthropic payload dictionary
optimized_payload = ToolRxAnthropic.optimize_payload(payload, top_k=5)
```

---

## Hosted Edge Gateway REST API

Base URL: `https://api.toolrx.io` (or local `http://127.0.0.1:8080`)

### 1. `POST /v1/route`
Route a query over a dynamic tool catalog or pre-indexed global catalog.

**Headers:**
```http
Authorization: Bearer <your_api_key>
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "Issue refund for charge ch_12345",
  "tools": [ ... ],
  "top_k": 3
}
```

**Response (200 OK):**
```json
{
  "query": "Issue refund for charge ch_12345",
  "selected_tools": ["refund_stripe_charge"],
  "scores": {"refund_stripe_charge": 15.0},
  "latency_us": 412.5,
  "total_tools": 50,
  "selected_tools_count": 1,
  "savings": {
    "tokens_saved": 5200,
    "cost_saved_usd": 0.013,
    "token_savings_pct": 94.5,
    "latency_us": 412.5
  }
}
```

### 2. `POST /v1/optimize/openai`
Drop-in payload optimizer for OpenAI-compatible proxies.

### 3. `GET /v1/metrics`
Retrieve cumulative token savings, dollar savings, and latency percentiles.

### 4. `GET /v1/health`
Health check endpoint returning system status and version.
