"""
Unit tests for ToolRouter core functionality.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from toolrx import ToolRouter
from toolrx.core.schema import ToolDefinition

class TestToolRouter(unittest.TestCase):

    def setUp(self):
        self.sample_tools = [
            {
                "name": "send_slack_message",
                "description": "Send a formatted notification message to a Slack channel",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string"},
                        "text": {"type": "string"}
                    },
                    "required": ["channel", "text"]
                },
                "tags": ["messaging", "slack"]
            },
            {
                "name": "create_stripe_refund",
                "description": "Issue refund for payment charge id",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "charge_id": {"type": "string"},
                        "amount": {"type": "integer"}
                    },
                    "required": ["charge_id"]
                },
                "tags": ["payments", "stripe"]
            },
            {
                "name": "query_database_table",
                "description": "Execute analytical SQL statement on postgres db",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string"}
                    },
                    "required": ["sql"]
                },
                "tags": ["database", "sql"]
            }
        ]
        self.router = ToolRouter(self.sample_tools)

    def test_routing_precision(self):
        result = self.router.route("Please send a message to #general in Slack", top_k=1)
        self.assertEqual(len(result.selected_tools), 1)
        self.assertEqual(result.selected_tools[0], "send_slack_message")
        self.assertGreater(result.token_savings_pct, 50.0)

    def test_sql_routing(self):
        result = self.router.route("SELECT * FROM users WHERE active = true", top_k=1)
        self.assertEqual(result.selected_tools[0], "query_database_table")

    def test_custom_rule_boost(self):
        # Add explicit regex rule
        self.router.add_rule(r"\bdispute\b", "create_stripe_refund", boost=25.0)
        result = self.router.route("Handle customer dispute case", top_k=1)
        self.assertEqual(result.selected_tools[0], "create_stripe_refund")

    def test_fallback_tools(self):
        self.router.set_fallback_tools(["send_slack_message"])
        # Query with zero relevance to any tool
        result = self.router.route("xyz123 unrelated extraterrestrial gibberish", top_k=1, min_score=100.0)
        self.assertEqual(result.selected_tools, ["send_slack_message"])

    def test_prune_tools_payload(self):
        pruned = self.router.prune_tools("Issue refund for customer", top_k=1)
        self.assertEqual(len(pruned), 1)
        self.assertEqual(pruned[0]["name"], "create_stripe_refund")

if __name__ == "__main__":
    unittest.main()
