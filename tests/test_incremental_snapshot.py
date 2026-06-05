# -*- coding: utf-8 -*-
"""Tests for runtime incremental snapshots."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from fileguard.capture.snapshot import SnapshotManager
from fileguard.models import FileEvent


class TestIncrementalSnapshot(unittest.TestCase):
    """Verify runtime snapshot deltas do not break baseline/restore."""

    def test_incremental_record_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "doc.txt"
            target.write_text("baseline\n", encoding="utf-8")
            manager = SnapshotManager(
                {
                    "backup_files": True,
                    "backup_dir": ".fileguard/backups",
                    "baseline_file": ".fileguard/baseline.json",
                    "incremental_file": ".fileguard/incremental.jsonl",
                }
            )
            manager.build_baseline(str(root))
            target.write_text("changed\n", encoding="utf-8")

            record = manager.update_incremental(
                FileEvent(datetime.now(), "modified", str(target), file_size=target.stat().st_size)
            )

            self.assertIsNotNone(record)
            self.assertEqual(len(manager.incremental_records), 1)
            self.assertTrue((root / ".fileguard" / "incremental.jsonl").exists())
            results = manager.restore(str(root / ".fileguard" / "baseline.json"), str(root))
            self.assertTrue(results[str(target.resolve())])


if __name__ == "__main__":
    unittest.main()
