# -*- coding: utf-8 -*-
"""Unit tests for HoneypotSentinel."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from fileguard.analyzers.honeypot import HoneypotSentinel
from fileguard.models import FileEvent


class TestHoneypotSentinel(unittest.TestCase):
    """Test honeypot deployment and trigger detection."""

    def setUp(self) -> None:
        """Create a sentinel with deterministic honeypot filenames."""
        self.sentinel = HoneypotSentinel(
            {
                "enabled": True,
                "weight": 5.0,
                "deploy_count": 2,
                "filename_templates": ["~$budget_draft.tmp", ".~lock.confidential.docx#"],
            }
        )

    def _event(
        self, src_path: Path, event_type: str = "modified", dest_path: Path | None = None
    ) -> FileEvent:
        """Build a FileEvent for honeypot tests."""
        return FileEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            src_path=str(src_path),
            dest_path=str(dest_path) if dest_path is not None else None,
            is_directory=False,
        )

    def test_deploy_honeypots_creates_files(self) -> None:
        """Deploying honeypots should create configured files exactly once."""
        with tempfile.TemporaryDirectory() as temp_dir:
            deployed = self.sentinel.deploy_honeypots(temp_dir)
            redeployed = self.sentinel.deploy_honeypots(temp_dir)

            self.assertEqual(len(deployed), 2)
            self.assertEqual(deployed, redeployed)
            for raw_path in deployed:
                path = Path(raw_path)
                self.assertTrue(path.exists())
                self.assertIn("FileGuard honeypot", path.read_text(encoding="utf-8"))

    def test_touching_honeypot_triggers_max_signal(self) -> None:
        """Any event on a deployed honeypot should produce a 10-point signal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            honeypot = Path(self.sentinel.deploy_honeypots(temp_dir)[0])

            signal = self.sentinel.analyze(self._event(honeypot))

            self.assertIsNotNone(signal)
            self.assertEqual(signal.signal_type, "honeypot_triggered")
            self.assertEqual(signal.value, 10.0)
            self.assertEqual(signal.evidence["honeypot_path"], str(honeypot.resolve()))

    def test_regular_file_does_not_trigger(self) -> None:
        """A normal file not in the honeypot set should not trigger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.sentinel.deploy_honeypots(temp_dir)
            normal_file = Path(temp_dir) / "normal.txt"
            normal_file.write_text("normal", encoding="utf-8")

            signal = self.sentinel.analyze(self._event(normal_file))

            self.assertIsNone(signal)

    def test_moved_to_or_from_honeypot_triggers(self) -> None:
        """Moved events should check both source and destination paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            honeypot = Path(self.sentinel.deploy_honeypots(temp_dir)[0])
            normal_file = Path(temp_dir) / "normal.txt"
            normal_file.write_text("normal", encoding="utf-8")

            from_signal = self.sentinel.analyze(
                self._event(honeypot, "moved", normal_file)
            )
            to_signal = self.sentinel.analyze(
                self._event(normal_file, "moved", honeypot)
            )

            self.assertIsNotNone(from_signal)
            self.assertIsNotNone(to_signal)
            self.assertEqual(from_signal.signal_type, "honeypot_triggered")
            self.assertEqual(to_signal.signal_type, "honeypot_triggered")


if __name__ == "__main__":
    unittest.main()
