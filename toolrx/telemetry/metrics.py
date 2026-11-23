"""
Client-side telemetry and audit logging for enterprise compliance.
"""

from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class ToolRxAuditEntry:
    query: str
    selected_tools: List[str]
    latency_us: float
    timestamp: float

class EnterpriseAuditor:
    """Zero-dependency audit logger for enterprise compliance and routing verifiability."""

    def __init__(self):
        self.logs: List[ToolRxAuditEntry] = []

    def record(self, entry: ToolRxAuditEntry) -> None:
        self.logs.append(entry)

    def export_summary(self) -> Dict[str, Any]:
        return {
            "total_audit_events": len(self.logs),
            "events": [
                {
                    "query": e.query,
                    "selected": e.selected_tools,
                    "latency_us": e.latency_us,
                    "timestamp": e.timestamp
                }
                for e in self.logs[-50:] # last 50 events
            ]
        }
