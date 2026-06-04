# -*- coding: utf-8 -*-
"""Unit tests for SensitivePathAnalyzer."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from fileguard.analyzers.sensitive_path import SensitivePathAnalyzer
from fileguard.models import FileEvent


class TestSensitivePathAnalyzer(unittest.TestCase):
    """Test sensitive path policy matching and time weighting."""

    def setUp(self) -> None:
        """Initialize policies used by the sensitive path analyzer tests."""
        self.analyzer = SensitivePathAnalyzer(
            {
                "enabled": True,
                "weight": 2.0,
                "policies": [
                    {
                        "name": "financial",
                        "pattern": "**/financial/**",
                        "risk_base": 6.0,
                        "time_restriction": {
                            "deny_hours": [0, 1, 2, 3, 4, 5, 22, 23],
                            "time_multiplier": 1.5,
                        },
                    },
                    {
                        "name": "config",
                        "pattern": "**/config/**",
                        "risk_base": 5.0,
                    },
                    {
                        "name": "keys",
                        "pattern": "**/*.pem|**/*.key|**/*.pfx",
                        "risk_base": 9.0,
                    },
                ],
            }
        )

    def _event(self, path: str, hour: int = 10) -> FileEvent:
        """Build a FileEvent with a fixed hour."""
        return FileEvent(
            timestamp=datetime(2026, 1, 1, hour, 0, 0),
            event_type="modified",
            src_path=path,
            is_directory=False,
        )

    def test_financial_path_hit(self) -> None:
        """A path under a financial directory should hit the financial policy."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "financial" / "budget.csv"
            path.parent.mkdir()

            signal = self.analyzer.analyze(self._event(str(path)))

            self.assertIsNotNone(signal)
            self.assertEqual(signal.signal_type, "policy_hit")
            self.assertEqual(signal.evidence["policy_name"], "financial")
            self.assertEqual(signal.evidence["pattern"], "**/financial/**")
            self.assertFalse(signal.evidence["time_restricted"])
            self.assertEqual(signal.value, 6.0)

    def test_config_path_hit(self) -> None:
        """A path under a config directory should hit the config policy."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config" / "database.conf"
            path.parent.mkdir()

            signal = self.analyzer.analyze(self._event(str(path)))

            self.assertIsNotNone(signal)
            self.assertEqual(signal.evidence["policy_name"], "config")
            self.assertEqual(signal.evidence["final_value"], 5.0)

    def test_pem_key_multi_pattern_hit(self) -> None:
        """Pipe-separated pem/key/pfx patterns should match either extension."""
        with tempfile.TemporaryDirectory() as temp_dir:
            key_path = Path(temp_dir) / "secrets" / "service.key"
            key_path.parent.mkdir()
            windows_style_path = str(key_path).replace("/", "\\")

            signal = self.analyzer.analyze(self._event(windows_style_path))

            self.assertIsNotNone(signal)
            self.assertEqual(signal.evidence["policy_name"], "keys")
            self.assertEqual(signal.evidence["pattern"], "**/*.key")
            self.assertEqual(signal.value, 9.0)

    def test_non_sensitive_path_does_not_trigger(self) -> None:
        """A normal document path should not match any policy."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "documents" / "readme.txt"
            path.parent.mkdir()

            signal = self.analyzer.analyze(self._event(str(path)))

            self.assertIsNone(signal)

    def test_denied_hour_applies_time_multiplier(self) -> None:
        """A financial path during denied hours should be weighted."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "financial" / "payroll.csv"
            path.parent.mkdir()

            signal = self.analyzer.analyze(self._event(str(path), hour=23))

            self.assertIsNotNone(signal)
            self.assertTrue(signal.evidence["time_restricted"])
            self.assertEqual(signal.evidence["risk_base"], 6.0)
            self.assertEqual(signal.evidence["final_value"], 9.0)
            self.assertEqual(signal.value, 9.0)


if __name__ == "__main__":
    unittest.main()
