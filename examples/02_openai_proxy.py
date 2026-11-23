"""
Example 2: Drop-in OpenAI Tool Calling Optimization
Demonstrates how ToolRx prunes OpenAI payload tools in-flight before API submission.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from toolrx.adapters import ToolRxOpenAI

def main():
    # Large tool catalog in standard OpenAI function format
    openai_payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a customer operations agent."},
            {"role": "user", "content": "Please issue a full refund for charge ch_992138 because customer was charged twice."}
        ],
        "tools": [
            {"type": "function", "function": {"name": f"unrelated_tool_{i}", "description": f"Internal helper tool {i}"}}
            for i in range(50)
        ] + [
            {
                "type": "function",
                "function": {
                    "name": "refund_stripe_charge",
                    "description": "Issue refund for payment charge or transaction",
                    "parameters": {
                        "type": "object",
                        "properties": {"charge_id": {"type": "string"}, "reason": {"type": "string"}},
                        "required": ["charge_id"]
                    }
                }
            }
        ]
    }

    print(f"Original Tools in Payload: {len(openai_payload['tools'])} tools")

    # One-line optimization interceptor
    optimized_payload = ToolRxOpenAI.optimize_payload(openai_payload, top_k=2)

    print(f"Optimized Tools in Payload: {len(optimized_payload['tools'])} tools")
    print(f"Selected Top Tool: {optimized_payload['tools'][0]['function']['name']}")
    print("Pruned ~96% of payload tools, preventing token bloat and LLM confusion!")

if __name__ == "__main__":
    main()
