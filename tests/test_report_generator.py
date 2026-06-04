# -*- coding: utf-8 -*-
"""System-level tests for HTML report generation."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from fileguard.models import AnalysisSignal, FileEvent, RiskAssessment
from fileguard.output.report import ReportGenerator


class TestReportGenerator(unittest.TestCase):
    """Verify ReportGenerator writes a useful HTML artifact."""

    def test_generate_report_with_single_alert(self) -> None:
        """Generated HTML should contain FileGuard and alert summary fields."""
        event = FileEvent(
            timestamp=datetime.now(),
            event_type="modified",
            src_path="experiments/sandbox/report-test.txt",
            is_directory=False,
        )
        signal = AnalysisSignal(
            analyzer_name="EntropyAnalyzer",
            signal_type="entropy_anomaly",
            value=8.0,
            weight=3.0,
            evidence={"entropy": 7.9},
        )
        assessment = RiskAssessment(
            event=event,
            signals=[signal],
            score=8.0,
            level="CRITICAL",
            timestamp=datetime.now(),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "report.html"
            ReportGenerator("templates/report.html", str(output)).generate([assessment])

            html = output.read_text(encoding="utf-8")
            self.assertTrue(output.exists())
            self.assertIn("FileGuard Security Analysis Report", html)
            self.assertIn("Total alerts", html)
            self.assertIn("CRITICAL", html)
            self.assertIn("EntropyAnalyzer", html)


if __name__ == "__main__":
    unittest.main()
