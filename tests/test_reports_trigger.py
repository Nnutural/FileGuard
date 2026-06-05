# -*- coding: utf-8 -*-
"""Tests for report trigger API."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from fileguard.api.server import ApiRuntimeState, create_app
from fileguard.scoring.alert import AlertManager


class TestReportsTrigger(unittest.TestCase):
    """Verify POST /api/reports generates a report."""

    def test_post_reports_writes_html(self) -> None:
        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            report = Path(temp_dir) / "report.html"
            state = ApiRuntimeState(
                alert_manager=AlertManager(),
                report_file=str(report),
                template_path="templates/report.html",
            )
            client = TestClient(create_app(runtime_state=state))

            response = client.post("/api/reports")

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["ok"])
            self.assertTrue(report.exists())
            self.assertIn("report_file", payload)


if __name__ == "__main__":
    unittest.main()
