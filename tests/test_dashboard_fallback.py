# -*- coding: utf-8 -*-
"""Tests for CLI dashboard fallback behavior."""

from __future__ import annotations

import unittest
from datetime import datetime

from fileguard.models import FileEvent, RiskAssessment
from fileguard.output.dashboard import Dashboard


class TestDashboardFallback(unittest.TestCase):
    """Dashboard updates should not require external monitor loops."""

    def test_dashboard_update_without_start_records_assessment(self) -> None:
        dashboard = Dashboard({})
        assessment = RiskAssessment(
            event=FileEvent(datetime.now(), "modified", "experiments/sandbox/demo.txt"),
            signals=[],
            score=0.0,
            level="LOW",
            timestamp=datetime.now(),
        )

        dashboard.update(assessment)

        self.assertEqual(sum(dashboard._level_counts.values()), 1)


if __name__ == "__main__":
    unittest.main()
