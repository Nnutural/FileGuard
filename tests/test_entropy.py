# -*- coding: utf-8 -*-
"""Unit tests for EntropyAnalyzer."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from fileguard.analyzers.entropy import EntropyAnalyzer
from fileguard.models import FileEvent


def _event(path: Path, event_type: str = "modified", is_directory: bool = False) -> FileEvent:
    """Build a FileEvent for analyzer tests."""
    return FileEvent(
        timestamp=datetime.now(),
        event_type=event_type,
        src_path=str(path),
        file_size=None if is_directory else (path.stat().st_size if path.exists() else None),
        is_directory=is_directory,
    )


class TestCalculateEntropy(unittest.TestCase):
    """Test the Shannon entropy helper."""

    def test_all_zero_bytes(self) -> None:
        """All-zero bytes should have 0 entropy."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(b"\x00" * 1024)
            path = f.name
        try:
            entropy = EntropyAnalyzer.calculate_entropy(path)
            self.assertAlmostEqual(entropy, 0.0, places=5)
        finally:
            os.unlink(path)

    def test_random_bytes(self) -> None:
        """Pseudo-random bytes should have high entropy."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(os.urandom(65536))
            path = f.name
        try:
            entropy = EntropyAnalyzer.calculate_entropy(path)
            self.assertGreater(entropy, 7.5)
            self.assertLessEqual(entropy, 8.0)
        finally:
            os.unlink(path)

    def test_plain_text(self) -> None:
        """Plain English text should have moderate entropy."""
        content = (
            "The quick brown fox jumps over the lazy dog. "
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
        ) * 50
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".txt", mode="w", encoding="utf-8"
        ) as f:
            f.write(content)
            path = f.name
        try:
            entropy = EntropyAnalyzer.calculate_entropy(path)
            self.assertGreater(entropy, 3.0)
            self.assertLess(entropy, 6.0)
        finally:
            os.unlink(path)

    def test_empty_file(self) -> None:
        """Empty files should have 0 entropy."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            path = f.name
        try:
            entropy = EntropyAnalyzer.calculate_entropy(path)
            self.assertAlmostEqual(entropy, 0.0, places=5)
        finally:
            os.unlink(path)


class TestEntropyAnalyzer(unittest.TestCase):
    """Test EntropyAnalyzer.analyze behavior."""

    def setUp(self) -> None:
        """Create an analyzer with a stable test configuration."""
        self.analyzer = EntropyAnalyzer(
            {
                "enabled": True,
                "weight": 3.0,
                "threshold": 6.5,
                "high_entropy_extensions": [".zip", ".jpg", ".png", ".pdf"],
            }
        )

    def test_low_entropy_text_file_does_not_trigger(self) -> None:
        """Low-entropy text content should not produce a signal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "notes.txt"
            path.write_text("hello fileguard\n" * 200, encoding="utf-8")

            signal = self.analyzer.analyze(_event(path, "modified"))

            self.assertIsNone(signal)

    def test_high_entropy_random_file_triggers(self) -> None:
        """High-entropy random content should produce an entropy anomaly signal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "payload.bin"
            path.write_bytes(os.urandom(65536))

            signal = self.analyzer.analyze(_event(path, "created"))

            self.assertIsNotNone(signal)
            self.assertEqual(signal.signal_type, "entropy_anomaly")
            self.assertGreater(signal.value, 6.0)
            self.assertLessEqual(signal.value, 10.0)
            self.assertEqual(signal.evidence["extension"], ".bin")
            self.assertEqual(signal.evidence["file_size"], path.stat().st_size)

    def test_high_entropy_allowlisted_extension_does_not_trigger(self) -> None:
        """High-entropy content with an allowlisted extension should be skipped."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "archive.zip"
            path.write_bytes(os.urandom(65536))

            signal = self.analyzer.analyze(_event(path, "created"))

            self.assertIsNone(signal)

    def test_deleted_moved_and_directory_events_do_not_trigger(self) -> None:
        """Unsupported event types and directory events should be ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "payload.bin"
            path.write_bytes(os.urandom(65536))
            directory = Path(temp_dir) / "folder"
            directory.mkdir()

            self.assertIsNone(self.analyzer.analyze(_event(path, "deleted")))
            self.assertIsNone(self.analyzer.analyze(_event(path, "moved")))
            self.assertIsNone(self.analyzer.analyze(_event(directory, "created", True)))


if __name__ == "__main__":
    unittest.main()
