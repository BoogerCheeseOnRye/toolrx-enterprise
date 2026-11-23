"""
Example 3: Interacting with ToolRx Hosted / On-Prem Gateway
Demonstrates HTTP client integration with API keys, metrics, and billing tracking.
"""

import sys
import os
import json
import urllib.request

GATEWAY_URL = "http://127.0.0.1:8080/v1/route"
API_KEY = "trx_live_pro_demo"

def route_via_gateway(query: str, tools: list, top_k: int = 3):
    payload = json.dumps({"query": query, "tools": tools, "top_k": top_k}).encode("utf-8")
    req = urllib.request.Request(
        GATEWAY_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print(f"ToolRx Gateway Target: {GATEWAY_URL}")
    print(f"Client API Key:        {API_KEY}")
    print("\nDeploy the server with: python -m toolrx.gateway.server")

if __name__ == "__main__":
    main()
