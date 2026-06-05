# -*- coding: utf-8 -*-
"""Tests for AlertManager escalation."""

from __future__ import annotations

import unittest
from datetime import datetime

from fileguard.models import AnalysisSignal, FileEvent, RiskAssessment
from fileguard.scoring.alert import AlertManager


class TestAlertEscalation(unittest.TestCase):
    """Verify compatible MEDIUM to HIGH escalation."""

    def _assessment(self, path: str) -> RiskAssessment:
        event = FileEvent(datetime.now(), "modified", path)
        signal = AnalysisSignal("SensitivePathAnalyzer", "policy_hit", 4.2, 2.0, {})
        return RiskAssessment(event, [signal], 4.2, "MEDIUM", datetime.now())

    def test_medium_alert_escalates_after_threshold(self) -> None:
        manager = AlertManager(
            cooldown_seconds=0,
            escalation_config={
                "enabled": True,
                "window_seconds": 60,
                "threshold": 2,
                "group_by": "signal_type",
            },
        )

        first = self._assessment("experiments/sandbox/a.txt")
        second = self._assessment("experiments/sandbox/b.txt")

        self.assertTrue(manager.process(first))
        self.assertEqual(first.level, "MEDIUM")
        self.assertTrue(manager.process(second))
        self.assertEqual(second.level, "HIGH")
        self.assertTrue(manager.get_metadata(second)["escalated"])
        self.assertEqual(manager.escalations_total, 1)


if __name__ == "__main__":
    unittest.main()
