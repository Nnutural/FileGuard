# -*- coding: utf-8 -*-
"""Tests for expanded API contract."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from fileguard.api.server import ApiRuntimeState, create_app
from fileguard.capture.snapshot import SnapshotManager
from fileguard.scoring.alert import AlertManager


class TestApiContract(unittest.TestCase):
    """Verify expanded API routes are stable on empty runtime state."""

    def test_get_routes_return_expected_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state = ApiRuntimeState(
                alert_manager=AlertManager(),
                snapshot_manager=SnapshotManager({}),
                report_file=str(Path(temp_dir) / "report.html"),
            )
            client = TestClient(create_app(runtime_state=state))
            expected = {
                "/api/status": ["events_total", "alerts_total", "highest_level"],
                "/api/events": ["total", "events"],
                "/api/alerts": ["total", "alerts", "by_level"],
                "/api/analyzers": ["total", "items"],
                "/api/snapshots": ["enabled", "incremental_records"],
                "/api/reports": ["report_file", "available", "events_total"],
            }
            for route, fields in expected.items():
                response = client.get(route)
                self.assertEqual(response.status_code, 200, route)
                payload = response.json()
                for field in fields:
                    self.assertIn(field, payload, route)


if __name__ == "__main__":
    unittest.main()
