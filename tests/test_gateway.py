"""
Integration tests for ToolRx Gateway HTTP server.
"""

import unittest
import threading
import json
import urllib.request
import urllib.error
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from toolrx.gateway.server import ToolRxGatewayServer

class TestGatewayServer(unittest.TestCase):
    server_thread = None
    gateway = None
    base_url = "http://127.0.0.1:8999"

    @classmethod
    def setUpClass(cls):
        sample_tools = [
            {"name": "fetch_user", "description": "Fetch user by ID", "parameters": {"type": "object", "properties": {"user_id": {"type": "string"}}}},
            {"name": "delete_user", "description": "Delete user by ID", "parameters": {"type": "object", "properties": {"user_id": {"type": "string"}}}}
        ]
        cls.gateway = ToolRxGatewayServer(host="127.0.0.1", port=8999, initial_tools=sample_tools)
        cls.server_thread = threading.Thread(target=cls.gateway.start, daemon=True)
        cls.server_thread.start()
        # Wait for server ready
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        if cls.gateway:
            cls.gateway.shutdown()

    def _request(self, method: str, path: str, data: dict = None, headers: dict = None):
        url = f"{self.base_url}{path}"
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                res_body = resp.read().decode("utf-8")
                return resp.status, json.loads(res_body)
        except urllib.error.HTTPError as e:
            res_body = e.read().decode("utf-8")
            return e.code, json.loads(res_body)

    def test_health_check(self):
        status, data = self._request("GET", "/v1/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "healthy")

    def test_unauthorized_route(self):
        status, data = self._request("POST", "/v1/route", data={"query": "test"})
        self.assertEqual(status, 401)

    def test_authorized_route(self):
        status, data = self._request(
            "POST",
            "/v1/route",
            data={"query": "Please fetch user account 123", "top_k": 1},
            headers={"Authorization": "Bearer trx_live_pro_demo"}
        )
        self.assertEqual(status, 200)
        self.assertIn("selected_tools", data)
        self.assertEqual(data["selected_tools"][0], "fetch_user")
        self.assertIn("savings", data)
        self.assertGreater(data["savings"]["tokens_saved"], 0)

    def test_metrics_reporting(self):
        status, data = self._request(
            "GET",
            "/v1/metrics",
            headers={"Authorization": "Bearer trx_live_pro_demo"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["tier"], "commercial_pro")
        self.assertGreater(data["telemetry"]["total_requests"], 0)

if __name__ == "__main__":
    unittest.main()
