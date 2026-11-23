"""
Example 1: Basic Deterministic Routing with Zero LLM Dependency
Demonstrates microsecond-level tool selection and prompt token savings.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from toolrx import ToolRouter

tools = [
    {
        "name": "search_customer_support_tickets",
        "description": "Search customer Zendesk tickets by email or issue keywords",
        "parameters": {
            "type": "object",
            "properties": {"email": {"type": "string"}, "query": {"type": "string"}},
            "required": ["query"]
        },
        "tags": ["support", "tickets"]
    },
    {
        "name": "issue_stripe_refund",
        "description": "Issue refund for payment charge or customer invoice",
        "parameters": {
            "type": "object",
            "properties": {"charge_id": {"type": "string"}, "amount": {"type": "number"}},
            "required": ["charge_id"]
        },
        "tags": ["billing", "stripe"]
    },
    {
        "name": "restart_backend_container",
        "description": "Perform rolling restart of microservice in cluster",
        "parameters": {
            "type": "object",
            "properties": {"service_name": {"type": "string"}},
            "required": ["service_name"]
        },
        "tags": ["devops", "cloud"]
    }
]

def main():
    router = ToolRouter(tools)

    user_query = "Can you check the open tickets for customer user@example.com?"
    print(f"User Query: '{user_query}'")

    result = router.route(user_query, top_k=1)

    print("\n--- Routing Result ---")
    print(f"Selected Tool:        {result.selected_tools[0]}")
    print(f"Routing Latency:      {result.latency_microseconds} μs")
    print(f"Evaluated Tools:      {result.all_evaluated_count}")
    print(f"Original Tokens:      {result.estimated_prompt_tokens_original} tokens")
    print(f"Routed Tokens:        {result.estimated_prompt_tokens_routed} tokens")
    print(f"Prompt Tokens Saved:  {result.tokens_saved} tokens ({result.token_savings_pct}%)")
    print(f"Decision Explanation: {result.explanation.get(result.selected_tools[0])}")

if __name__ == "__main__":
    main()
