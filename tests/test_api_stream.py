# -*- coding: utf-8 -*-
"""Tests for API Server-Sent Events."""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from fileguard.api.server import ApiRuntimeState, create_app


class TestApiStream(unittest.TestCase):
    """Verify the SSE endpoint produces an initial status event."""

    def test_stream_yields_status_event(self) -> None:
        client = TestClient(create_app(runtime_state=ApiRuntimeState()))
        with client.stream("GET", "/api/stream?once=true") as response:
            self.assertEqual(response.status_code, 200)
            lines = []
            for line in response.iter_lines():
                lines.append(line)
                if line == "event: status":
                    break
            self.assertIn("event: status", lines)


if __name__ == "__main__":
    unittest.main()
