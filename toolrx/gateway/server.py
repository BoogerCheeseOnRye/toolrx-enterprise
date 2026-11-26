"""
ToolRx Edge HTTP Gateway Server.
High-throughput, zero-dependency REST API wrapper for commercial routing.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
from typing import Dict, Any, Optional
from ..compat import ToolRouter
from .auth import AuthManager
from .telemetry import TelemetryCollector

class GatewayRequestHandler(BaseHTTPRequestHandler):
    auth_manager: AuthManager = AuthManager()
    telemetry: TelemetryCollector = TelemetryCollector()
    global_router: Optional[ToolRouter] = None

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress standard stderr access logging for maximum performance."""
        return

    def _send_json(self, status: int, data: Dict[str, Any]) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Powered-By", "ToolRx-Edge/1.0.0")
        self.end_headers()
        self.wfile.write(payload)

    def _get_api_key(self) -> Optional[str]:
        auth = self.headers.get("Authorization")
        if auth:
            return auth
        return self.headers.get("X-API-Key")

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/v1/health":
            self._send_json(200, {
                "status": "healthy",
                "service": "toolrx-edge-gateway",
                "version": "1.0.0"
            })
            return

        if parsed.path == "/v1/metrics":
            key = self._get_api_key()
            record = self.auth_manager.validate_key(key)
            if not record:
                self._send_json(401, {"error": "Unauthorized: valid API key required"})
                return

            self._send_json(200, {
                "tier": record.tier,
                "customer_id": record.customer_id,
                "telemetry": self.telemetry.get_summary()
            })
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)

        key = self._get_api_key()
        record = self.auth_manager.validate_key(key)
        if not record:
            self._send_json(401, {"error": "Unauthorized: missing or invalid API key"})
            return

        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len)
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON in request body"})
            return

        if parsed.path == "/v1/route":
            query = payload.get("query", "")
            tools = payload.get("tools", [])
            top_k = payload.get("top_k", 3)
            min_score = payload.get("min_score", 1.0)

            if not query:
                self._send_json(400, {"error": "Missing required field 'query'"})
                return

            if tools:
                router = ToolRouter(tools)
            elif self.global_router:
                router = self.global_router
            else:
                self._send_json(400, {"error": "No tools supplied and no global tools registered"})
                return

            result = router.route(query, top_k=top_k, min_score=min_score)
            savings = self.telemetry.record_routing_event(
                tokens_evaluated=result.estimated_prompt_tokens_original,
                tokens_routed=result.estimated_prompt_tokens_routed,
                latency_us=result.latency_microseconds
            )

            self._send_json(200, {
                "query": result.query,
                "selected_tools": result.selected_tools,
                "scores": result.scores,
                "latency_us": result.latency_microseconds,
                "total_tools": result.all_evaluated_count,
                "selected_tools_count": result.selected_count,
                "savings": savings,
                "explanation": result.explanation
            })
            return

        elif parsed.path == "/v1/optimize/openai":
            # Transparent proxy optimizer for OpenAI payloads
            openai_payload = payload.get("payload", {})
            top_k = payload.get("top_k", 5)
            from ..adapters.openai_adapter import ToolRxOpenAI

            optimized = ToolRxOpenAI.optimize_payload(openai_payload, top_k=top_k)
            orig_tools_count = len(openai_payload.get("tools", []))
            opt_tools_count = len(optimized.get("tools", []))

            self._send_json(200, {
                "optimized_payload": optimized,
                "original_tools_count": orig_tools_count,
                "optimized_tools_count": opt_tools_count,
                "tools_pruned": orig_tools_count - opt_tools_count
            })
            return

        self._send_json(404, {"error": "Endpoint not found"})

class ToolRxGatewayServer:
    """Server runner for ToolRx Edge Gateway."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8080, initial_tools: Optional[list] = None):
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        if initial_tools:
            GatewayRequestHandler.global_router = ToolRouter(initial_tools)

    def start(self) -> None:
        self.server = HTTPServer((self.host, self.port), GatewayRequestHandler)
        print(f"[ToolRx Gateway] Listening on http://{self.host}:{self.port}")
        self.server.serve_forever()

    def shutdown(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
