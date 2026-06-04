# -*- coding: utf-8 -*-
"""Unit tests for HashDiffChecker.analyze."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from fileguard.analyzers.hash_diff import HashDiffChecker
from fileguard.models import FileEvent


class TestHashDiffCheckerAnalyze(unittest.TestCase):
    """Test lightweight in-memory SHA-256 baseline behavior."""

    def setUp(self) -> None:
        """Initialize a fresh checker for each test."""
        self.checker = HashDiffChecker({"enabled": True, "weight": 1.5})

    def _event(self, path: Path, event_type: str = "modified", is_directory: bool = False) -> FileEvent:
        """Build a FileEvent for hash diff tests."""
        return FileEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            src_path=str(path),
            file_size=None if is_directory else (path.stat().st_size if path.exists() else None),
            is_directory=is_directory,
        )

    def test_first_observation_sets_baseline_without_signal(self) -> None:
        """First observation should establish a baseline only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "file.txt"
            path.write_text("initial", encoding="utf-8")

            signal = self.checker.analyze(self._event(path, "created"))

            self.assertIsNone(signal)
            self.assertIn(str(path.resolve()), self.checker._known_hashes)

    def test_unchanged_content_does_not_trigger(self) -> None:
        """A later event with identical content should not trigger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "file.txt"
            path.write_text("same", encoding="utf-8")
            self.assertIsNone(self.checker.analyze(self._event(path, "created")))

            signal = self.checker.analyze(self._event(path, "modified"))

            self.assertIsNone(signal)

    def test_changed_content_triggers(self) -> None:
        """A content hash change should produce a hash_changed signal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "file.txt"
            path.write_text("before", encoding="utf-8")
            self.assertIsNone(self.checker.analyze(self._event(path, "created")))
            path.write_text("after", encoding="utf-8")

            signal = self.checker.analyze(self._event(path, "modified"))

            self.assertIsNotNone(signal)
            self.assertEqual(signal.signal_type, "hash_changed")
            self.assertEqual(signal.value, 5.0)
            self.assertNotEqual(signal.evidence["old_hash"], signal.evidence["new_hash"])
            self.assertEqual(signal.evidence["file_size"], path.stat().st_size)

    def test_deleted_and_directory_events_do_not_trigger(self) -> None:
        """Deleted and directory events should be ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir) / "folder"
            directory.mkdir()
            missing = Path(temp_dir) / "missing.txt"

            self.assertIsNone(self.checker.analyze(self._event(missing, "deleted")))
            self.assertIsNone(self.checker.analyze(self._event(directory, "modified", True)))


if __name__ == "__main__":
    unittest.main()
