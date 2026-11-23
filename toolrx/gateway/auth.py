"""
API Key authentication and tier rate limit validation for ToolRx Hosted Gateway.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import time

@dataclass
class TierLimits:
    tier_name: str
    max_monthly_requests: int
    rate_limit_per_second: int
    allowed_enterprise_features: bool

TIER_PLANS = {
    "developer_free": TierLimits("developer_free", max_monthly_requests=10_000, rate_limit_per_second=10, allowed_enterprise_features=False),
    "commercial_pro": TierLimits("commercial_pro", max_monthly_requests=1_000_000, rate_limit_per_second=100, allowed_enterprise_features=True),
    "enterprise_scale": TierLimits("enterprise_scale", max_monthly_requests=-1, rate_limit_per_second=1_000, allowed_enterprise_features=True),
}

@dataclass
class KeyRecord:
    key: str
    customer_id: str
    tier: str
    requests_used: int = 0
    created_at: float = 0.0

class AuthManager:
    """In-memory key validator with tier enforcement."""

    def __init__(self):
        self._keys: Dict[str, KeyRecord] = {
            "trx_live_dev_testkey": KeyRecord("trx_live_dev_testkey", "cust_dev_001", "developer_free", 0, time.time()),
            "trx_live_pro_demo": KeyRecord("trx_live_pro_demo", "cust_pro_002", "commercial_pro", 0, time.time()),
            "trx_live_ent_vip": KeyRecord("trx_live_ent_vip", "cust_ent_003", "enterprise_scale", 0, time.time()),
        }

    def register_key(self, api_key: str, customer_id: str, tier: str = "commercial_pro") -> KeyRecord:
        record = KeyRecord(key=api_key, customer_id=customer_id, tier=tier, created_at=time.time())
        self._keys[api_key] = record
        return record

    def validate_key(self, api_key: Optional[str]) -> Optional[KeyRecord]:
        """Validate key and return record if active."""
        if not api_key:
            return None
        # Handle Bearer token prefix
        clean_key = api_key.replace("Bearer ", "").strip()
        record = self._keys.get(clean_key)
        if record:
            record.requests_used += 1
            return record
        return None
