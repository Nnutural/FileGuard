# -*- coding: utf-8 -*-
"""Unit tests for snapshot and SHA-256 helpers."""

from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from fileguard.analyzers.hash_diff import HashDiffChecker
from fileguard.capture.snapshot import SnapshotManager


class TestComputeSha256(unittest.TestCase):
    """Test SHA-256 helper behavior."""

    def test_known_content(self) -> None:
        """Known content should produce the expected digest."""
        content = b"Hello, FileGuard!"
        expected = hashlib.sha256(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(content)
            path = f.name
        try:
            result = HashDiffChecker.compute_sha256(path)
            self.assertEqual(result, expected)
        finally:
            os.unlink(path)

    def test_empty_file(self) -> None:
        """An empty file should match the SHA-256 of empty bytes."""
        expected = hashlib.sha256(b"").hexdigest()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            path = f.name
        try:
            result = HashDiffChecker.compute_sha256(path)
            self.assertEqual(result, expected)
        finally:
            os.unlink(path)

    def test_large_file(self) -> None:
        """Large files should be hashed correctly with chunked reads."""
        content = os.urandom(256 * 1024)
        expected = hashlib.sha256(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(content)
            path = f.name
        try:
            result = HashDiffChecker.compute_sha256(path)
            self.assertEqual(result, expected)
        finally:
            os.unlink(path)


class TestSnapshotManager(unittest.TestCase):
    """Test baseline creation and restore verification."""

    def test_build_baseline_and_restore_file(self) -> None:
        """A backed-up file should restore to its baseline content and hash."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "documents" / "report.txt"
            target.parent.mkdir()
            target.write_text("baseline content\n", encoding="utf-8")

            manager = SnapshotManager(
                {
                    "backup_files": True,
                    "backup_dir": ".fileguard/backups",
                    "baseline_file": ".fileguard/baseline.json",
                    "max_file_size_mb": 1,
                }
            )
            baseline = manager.build_baseline(str(root))
            snapshot_path = root / ".fileguard" / "baseline.json"
            expected_hash = HashDiffChecker.compute_sha256(target)

            self.assertIn(str(target.resolve()), baseline)
            self.assertTrue(snapshot_path.exists())
            self.assertEqual(baseline[str(target.resolve())].sha256, expected_hash)
            self.assertIsNotNone(baseline[str(target.resolve())].content_backup_path)

            target.write_text("changed content\n", encoding="utf-8")
            results = manager.restore(str(snapshot_path), str(root))

            self.assertTrue(results[str(target.resolve())])
            self.assertEqual(target.read_text(encoding="utf-8"), "baseline content\n")
            self.assertEqual(HashDiffChecker.compute_sha256(target), expected_hash)


if __name__ == "__main__":
    unittest.main()
