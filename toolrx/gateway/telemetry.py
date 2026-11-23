"""
Telemetry, cost savings calculator, and performance metrics for ToolRx Gateway.
"""

from dataclasses import dataclass, field
import threading
from typing import Dict, Any, List

# Estimated prompt token cost per 1M tokens ($2.50 / 1M tokens for standard frontier models like GPT-4o)
DEFAULT_COST_PER_MILLION_INPUT_TOKENS = 2.50

@dataclass
class GatewayMetrics:
    total_requests: int = 0
    total_tokens_evaluated: int = 0
    total_tokens_routed: int = 0
    total_tokens_saved: int = 0
    total_usd_saved: float = 0.0
    latencies_us: List[float] = field(default_factory=list)

class TelemetryCollector:
    """Thread-safe telemetry accumulator for gateway monetization reporting."""

    def __init__(self, cost_per_m_tokens: float = DEFAULT_COST_PER_MILLION_INPUT_TOKENS):
        self.cost_per_m_tokens = cost_per_m_tokens
        self.metrics = GatewayMetrics()
        self._lock = threading.Lock()

    def record_routing_event(
        self,
        tokens_evaluated: int,
        tokens_routed: int,
        latency_us: float
    ) -> Dict[str, Any]:
        with self._lock:
            self.metrics.total_requests += 1
            self.metrics.total_tokens_evaluated += tokens_evaluated
            self.metrics.total_tokens_routed += tokens_routed

            saved = max(0, tokens_evaluated - tokens_routed)
            self.metrics.total_tokens_saved += saved

            cost_saved = (saved / 1_000_000.0) * self.cost_per_m_tokens
            self.metrics.total_usd_saved += cost_saved

            if len(self.metrics.latencies_us) < 10_000:
                self.metrics.latencies_us.append(latency_us)

            return {
                "tokens_saved": saved,
                "cost_saved_usd": round(cost_saved, 6),
                "token_savings_pct": round((saved / tokens_evaluated * 100.0), 2) if tokens_evaluated else 0.0,
                "latency_us": round(latency_us, 2)
            }

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            lat = sorted(self.metrics.latencies_us) if self.metrics.latencies_us else [0.0]
            p50 = lat[int(len(lat) * 0.50)]
            p95 = lat[int(len(lat) * 0.95)]
            p99 = lat[int(len(lat) * 0.99)]

            return {
                "total_requests": self.metrics.total_requests,
                "total_tokens_evaluated": self.metrics.total_tokens_evaluated,
                "total_tokens_routed": self.metrics.total_tokens_routed,
                "total_tokens_saved": self.metrics.total_tokens_saved,
                "total_usd_saved": round(self.metrics.total_usd_saved, 4),
                "latency_p50_us": round(p50, 2),
                "latency_p95_us": round(p95, 2),
                "latency_p99_us": round(p99, 2),
            }
