"""
Unit tests for OpenAI and Anthropic adapters.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from toolrx.adapters import ToolRxOpenAI, ToolRxAnthropic, GenericToolAdapter

class TestAdapters(unittest.TestCase):

    def setUp(self):
        self.openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": "lookup_user_account",
                    "description": "Find user profile by account ID or email",
                    "parameters": {
                        "type": "object",
                        "properties": {"user_id": {"type": "string"}},
                        "required": ["user_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "issue_charge_refund",
                    "description": "Refund Stripe charge",
                    "parameters": {
                        "type": "object",
                        "properties": {"charge_id": {"type": "string"}},
                        "required": ["charge_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "restart_k8s_deployment",
                    "description": "Restart kubernetes containers",
                    "parameters": {"type": "object", "properties": {"app": {"type": "string"}}}
                }
            }
        ]

    def test_openai_payload_optimization(self):
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Please refund customer charge ch_88291"}
            ],
            "tools": self.openai_tools
        }

        optimized = ToolRxOpenAI.optimize_payload(payload, top_k=1)
        self.assertEqual(len(optimized["tools"]), 1)
        self.assertEqual(optimized["tools"][0]["function"]["name"], "issue_charge_refund")

    def test_anthropic_payload_optimization(self):
        anthropic_tools = [
            {"name": "fetch_logs", "description": "Fetch application error logs", "input_schema": {}},
            {"name": "deploy_service", "description": "Deploy git commit to production", "input_schema": {}}
        ]
        payload = {
            "model": "claude-3-5-sonnet",
            "messages": [
                {"role": "user", "content": "Look at the error logs for the web container"}
            ],
            "tools": anthropic_tools
        }
        optimized = ToolRxAnthropic.optimize_payload(payload, top_k=1)
        self.assertEqual(len(optimized["tools"]), 1)
        self.assertEqual(optimized["tools"][0]["name"], "fetch_logs")

    def test_generic_adapter(self):
        tools = [{"name": "math_eval"}, {"name": "web_search"}]
        filter_fn = GenericToolAdapter.wrap_agent_toolset(
            tools=tools,
            schema_extractor=lambda t: {"name": t["name"], "description": t["name"]},
            top_k=1
        )
        selected = filter_fn("evaluate math formula 2 + 2")
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["name"], "math_eval")

if __name__ == "__main__":
    unittest.main()
