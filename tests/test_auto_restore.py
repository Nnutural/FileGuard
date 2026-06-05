# -*- coding: utf-8 -*-
"""Tests for sandbox-bound defensive auto-restore."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from fileguard.analyzers.hash_diff import HashDiffChecker
from fileguard.capture.snapshot import SnapshotManager
from fileguard.models import AnalysisSignal, FileEvent, RiskAssessment


class TestAutoRestore(unittest.TestCase):
    """Verify dry-run, real restore, and boundary rejection."""

    def _critical(self, path: Path) -> RiskAssessment:
        event = FileEvent(datetime.now(), "modified", str(path), file_size=path.stat().st_size)
        signal = AnalysisSignal("EntropyAnalyzer", "entropy_anomaly", 9.0, 3.0, {})
        return RiskAssessment(event, [signal], 9.0, "CRITICAL", datetime.now())

    def test_dry_run_and_real_restore(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox = Path(temp_dir) / "experiments" / "sandbox"
            sandbox.mkdir(parents=True)
            target = sandbox / "doc.txt"
            target.write_text("baseline\n", encoding="utf-8")
            manager = SnapshotManager(
                {
                    "backup_files": True,
                    "backup_dir": ".fileguard/backups",
                    "baseline_file": ".fileguard/baseline.json",
                }
            )
            manager.build_baseline(str(sandbox))
            expected = HashDiffChecker.compute_sha256(target)
            target.write_text("changed\n", encoding="utf-8")

            dry = manager.auto_restore_if_needed(self._critical(target), str(sandbox), enabled=True, dry_run=True)
            self.assertIsNotNone(dry)
            self.assertFalse(bool(dry["restored"]))
            self.assertEqual(target.read_text(encoding="utf-8"), "changed\n")

            real = manager.auto_restore_if_needed(self._critical(target), str(sandbox), enabled=True, dry_run=False)
            self.assertIsNotNone(real)
            self.assertTrue(bool(real["restored"]))
            self.assertEqual(HashDiffChecker.compute_sha256(target), expected)

    def test_outside_sandbox_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sandbox = root / "experiments" / "sandbox"
            sandbox.mkdir(parents=True)
            outside = root / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            manager = SnapshotManager({})

            result = manager.auto_restore_if_needed(self._critical(outside), str(sandbox), enabled=True)

            self.assertIsNotNone(result)
            self.assertIn("outside", str(result["reason"]))


if __name__ == "__main__":
    unittest.main()
