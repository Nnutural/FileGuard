# -*- coding: utf-8 -*-
"""Unit tests for AnalysisPipeline scheduling."""

from __future__ import annotations

import unittest
from datetime import datetime

from fileguard.analyzers.base import BaseAnalyzer
from fileguard.models import AnalysisSignal, FileEvent
from fileguard.pipeline import AnalysisPipeline
from fileguard.scoring.alert import AlertManager
from fileguard.scoring.scorer import RiskScorer


class _SignalAnalyzer(BaseAnalyzer):
    """Small analyzer used to prove pipeline dispatch."""

    @property
    def name(self) -> str:
        """Return the test analyzer name."""
        return "SignalAnalyzer"

    def analyze(self, event: FileEvent) -> AnalysisSignal | None:
        """Always emit one signal."""
        return self.create_signal("test_signal", 8.0, {"path": event.src_path})


class TestAnalysisPipeline(unittest.TestCase):
    """Test pipeline analyzer scheduling, scoring, and alert recording."""

    def test_process_event_collects_scores_and_alerts(self) -> None:
        """Pipeline should call analyzers, score signals, and update alerts."""
        event = FileEvent(
            timestamp=datetime.now(),
            event_type="modified",
            src_path="test.txt",
            is_directory=False,
        )
        alert_manager = AlertManager(cooldown_seconds=0)
        pipeline = AnalysisPipeline(
            analyzers=[_SignalAnalyzer({"weight": 2.0})],
            scorer=RiskScorer(
                {
                    "low": [0, 3.0],
                    "medium": [3.0, 5.0],
                    "high": [5.0, 7.0],
                    "critical": [7.0, 10.0],
                }
            ),
            alert_manager=alert_manager,
        )

        assessment = pipeline.process_event(event)

        self.assertEqual(len(assessment.signals), 1)
        self.assertEqual(assessment.signals[0].signal_type, "test_signal")
        self.assertEqual(assessment.score, 8.0)
        self.assertEqual(assessment.level, "CRITICAL")
        self.assertEqual(len(alert_manager.get_timeline()), 1)


if __name__ == "__main__":
    unittest.main()
