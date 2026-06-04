# -*- coding: utf-8 -*-
"""System-level tests for JSONL event logging."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from fileguard.models import AnalysisSignal, FileEvent, RiskAssessment
from fileguard.output.logger import EventLogger


class TestEventLogger(unittest.TestCase):
    """Verify JSONL logger writes valid serialized assessments."""

    def test_log_writes_valid_json_line(self) -> None:
        """A logged assessment should be one valid JSON object per line."""
        event = FileEvent(
            timestamp=datetime.now(),
            event_type="created",
            src_path="experiments/sandbox/logger-test.txt",
            is_directory=False,
        )
        signal = AnalysisSignal(
            analyzer_name="SensitivePathAnalyzer",
            signal_type="policy_hit",
            value=6.0,
            weight=2.0,
            evidence={"policy_name": "test"},
        )
        assessment = RiskAssessment(
            event=event,
            signals=[signal],
            score=6.0,
            level="HIGH",
            timestamp=datetime.now(),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "events.jsonl"
            with EventLogger(str(log_path)) as logger:
                logger.log(assessment)

            lines = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            payload = json.loads(lines[0])
            self.assertIn("event", payload)
            self.assertIn("signals", payload)
            self.assertIsInstance(payload["timestamp"], str)
            self.assertIsInstance(payload["event"]["timestamp"], str)
            self.assertEqual(payload["signals"][0]["signal_type"], "policy_hit")


if __name__ == "__main__":
    unittest.main()
