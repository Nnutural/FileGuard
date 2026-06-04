# -*- coding: utf-8 -*-
"""Unit tests for FuzzyHashAnalyzer."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from fileguard.analyzers.fuzzy_hash import FuzzyHashAnalyzer
from fileguard.models import FileEvent


class TestFuzzyHashAnalyzer(unittest.TestCase):
    """Test block-hash similarity behavior."""

    def setUp(self) -> None:
        """Initialize a fuzzy hash analyzer with small test blocks."""
        self.analyzer = FuzzyHashAnalyzer(
            {
                "enabled": True,
                "weight": 3.0,
                "block_size": 8,
                "similarity_threshold": 0.3,
            }
        )

    def _event(self, path: Path, event_type: str = "modified") -> FileEvent:
        """Build a FileEvent for fuzzy hash tests."""
        return FileEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            src_path=str(path),
            file_size=path.stat().st_size if path.exists() else None,
            is_directory=False,
        )

    def test_first_observation_does_not_trigger(self) -> None:
        """The first modified event should only establish the block baseline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "file.bin"
            path.write_bytes(b"A" * 64)

            signal = self.analyzer.analyze(self._event(path))

            self.assertIsNone(signal)
            self.assertIn(str(path.resolve()), self.analyzer._block_baseline)

    def test_small_append_keeps_similarity_high(self) -> None:
        """A small append that preserves most blocks should not trigger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "file.bin"
            path.write_bytes(b"A" * 64)
            self.assertIsNone(self.analyzer.analyze(self._event(path)))
            path.write_bytes(b"A" * 72)

            signal = self.analyzer.analyze(self._event(path))

            self.assertIsNone(signal)

    def test_complete_replacement_triggers_similarity_drop(self) -> None:
        """Replacing all content should produce a similarity_drop signal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "file.bin"
            path.write_bytes(b"A" * 64)
            self.assertIsNone(self.analyzer.analyze(self._event(path)))
            path.write_bytes(b"B" * 64)

            signal = self.analyzer.analyze(self._event(path))

            self.assertIsNotNone(signal)
            self.assertEqual(signal.signal_type, "similarity_drop")
            self.assertEqual(signal.evidence["similarity"], 0.0)
            self.assertEqual(signal.evidence["old_block_count"], 8)
            self.assertEqual(signal.evidence["new_block_count"], 8)

    def test_empty_and_small_files_do_not_crash(self) -> None:
        """Empty and very small files should be handled without exceptions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_path = Path(temp_dir) / "empty.bin"
            empty_path.write_bytes(b"")

            self.assertIsNone(self.analyzer.analyze(self._event(empty_path)))
            self.assertIsNone(self.analyzer.analyze(self._event(empty_path)))

            small_path = Path(temp_dir) / "small.bin"
            small_path.write_bytes(b"x")
            self.assertIsNone(self.analyzer.analyze(self._event(small_path)))
            small_path.write_bytes(b"yz")
            signal = self.analyzer.analyze(self._event(small_path))

            self.assertIsNotNone(signal)
            self.assertEqual(signal.signal_type, "similarity_drop")


if __name__ == "__main__":
    unittest.main()
