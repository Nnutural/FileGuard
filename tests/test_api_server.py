# -*- coding: utf-8 -*-
"""System-level tests for FastAPI routes."""

from __future__ import annotations

import unittest
from datetime import datetime

from fastapi.testclient import TestClient

from fileguard.api.server import ApiRuntimeState, create_app
from fileguard.models import AnalysisSignal, FileEvent, RiskAssessment
from fileguard.scoring.alert import AlertManager


class TestApiServer(unittest.TestCase):
    """Verify API routes return stable JSON responses."""

    def test_empty_runtime_routes_return_200(self) -> None:
        """Empty runtime state should not produce 500 responses."""
        client = TestClient(create_app(runtime_state=ApiRuntimeState()))

        for route in ("/api/status", "/api/events", "/api/alerts"):
            response = client.get(route)
            self.assertEqual(response.status_code, 200)
            self.assertIsInstance(response.json(), dict)

        status = client.get("/api/status").json()
        self.assertIn("running", status)
        self.assertIn("events_processed", status)

        events = client.get("/api/events").json()
        self.assertEqual(events["total"], 0)
        self.assertIn("events", events)

        alerts = client.get("/api/alerts").json()
        self.assertEqual(alerts["total"], 0)
        self.assertIn("alerts", alerts)

    def test_runtime_state_routes_include_events_and_alerts(self) -> None:
        """Runtime state should expose recent events and AlertManager timeline."""
        event = FileEvent(
            timestamp=datetime.now(),
            event_type="modified",
            src_path="sandbox/file.txt",
            is_directory=False,
        )
        signal = AnalysisSignal(
            analyzer_name="TestAnalyzer",
            signal_type="test_signal",
            value=8.0,
            weight=1.0,
            evidence={"path": event.src_path},
        )
        assessment = RiskAssessment(
            event=event,
            signals=[signal],
            score=8.0,
            level="CRITICAL",
            timestamp=datetime.now(),
        )
        alert_manager = AlertManager(cooldown_seconds=0)
        self.assertTrue(alert_manager.process(assessment))

        state = ApiRuntimeState(running=True, watch_dirs=["sandbox"], alert_manager=alert_manager)
        state.record_event(event, queue_size=2)
        client = TestClient(create_app(runtime_state=state))

        status = client.get("/api/status").json()
        self.assertTrue(status["running"])
        self.assertEqual(status["events_processed"], 1)
        self.assertEqual(status["queue_size"], 2)

        events = client.get("/api/events").json()
        self.assertEqual(events["total"], 1)
        self.assertEqual(events["events"][0]["event_type"], "modified")

        alerts = client.get("/api/alerts").json()
        self.assertEqual(alerts["total"], 1)
        self.assertEqual(alerts["alerts"][0]["level"], "CRITICAL")
        self.assertEqual(alerts["alerts"][0]["analyzers"], ["TestAnalyzer"])


if __name__ == "__main__":
    unittest.main()
