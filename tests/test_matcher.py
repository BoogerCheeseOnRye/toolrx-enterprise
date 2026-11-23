"""
Unit tests for deterministic matcher, negations, and entity detection.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from toolrx.router import ToolRouter

class TestMatcherFeatures(unittest.TestCase):

    def setUp(self):
        self.tools = [
            {
                "name": "execute_payment_transfer",
                "description": "Send funds or execute payment wire",
                "parameters": {"type": "object", "properties": {"amount": {"type": "number"}}},
                "tags": ["payment", "transfer"]
            },
            {
                "name": "preview_payment_transfer",
                "description": "Dry-run and preview payment transfer details without executing",
                "parameters": {"type": "object", "properties": {"amount": {"type": "number"}}},
                "tags": ["payment", "preview"]
            },
            {
                "name": "send_email_receipt",
                "description": "Email PDF receipt to customer recipient",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipient": {"type": "string"},
                        "email": {"type": "string"}
                    }
                },
                "tags": ["email", "receipt"]
            }
        ]
        self.router = ToolRouter(self.tools)

    def test_negation_suppression(self):
        # Explicit negation: "do not transfer" should penalize execute_payment_transfer and favor preview
        res = self.router.route("Preview invoice for $500, do not execute transfer", top_k=1)
        self.assertEqual(res.selected_tools[0], "preview_payment_transfer")

    def test_entity_parameter_matching(self):
        res = self.router.route("Send statement to john@example.com", top_k=1)
        self.assertEqual(res.selected_tools[0], "send_email_receipt")
        self.assertTrue(any("email" in exp for exp in res.explanation["send_email_receipt"]))

    def test_stemming_match(self):
        # Query uses plural 'receipts' while tool description has 'receipt'
        res = self.router.route("Where are my receipts?", top_k=1)
        self.assertEqual(res.selected_tools[0], "send_email_receipt")

if __name__ == "__main__":
    unittest.main()
