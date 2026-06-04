# -*- coding: utf-8 -*-
"""Lightweight CLI handler integration tests."""

from __future__ import annotations

import argparse
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from fileguard.cli import _handle_report, _handle_snapshot
from fileguard.models import FileEvent, RiskAssessment
from fileguard.output.logger import EventLogger


class TestCliIntegration(unittest.TestCase):
    """Verify non-monitor CLI handlers run against temporary files."""

    def test_snapshot_command_builds_baseline(self) -> None:
        """The snapshot handler should create a baseline for a temp watch dir."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            watch_dir = root / "watch"
            watch_dir.mkdir()
            (watch_dir / "file.txt").write_text("baseline\n", encoding="utf-8")
            config_path = self._write_config(root, watch_dir)
            output_path = root / "baseline.json"

            _handle_snapshot(
                argparse.Namespace(config=str(config_path), output=str(output_path))
            )

            self.assertTrue(output_path.exists())
            self.assertIn("file.txt", output_path.read_text(encoding="utf-8"))

    def test_report_command_generates_html(self) -> None:
        """The report handler should convert JSONL assessments to HTML."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            watch_dir = root / "watch"
            watch_dir.mkdir()
            output_dir = root / "out"
            output_dir.mkdir()
            config_path = self._write_config(root, watch_dir)
            log_path = output_dir / "events.jsonl"
            report_path = output_dir / "report.html"

            event = FileEvent(
                timestamp=datetime.now(),
                event_type="modified",
                src_path=str(watch_dir / "file.txt"),
                is_directory=False,
            )
            assessment = RiskAssessment(
                event=event,
                signals=[],
                score=0.0,
                level="LOW",
                timestamp=datetime.now(),
            )
            with EventLogger(str(log_path)) as logger:
                logger.log(assessment)

            _handle_report(
                argparse.Namespace(
                    config=str(config_path),
                    log_file=str(log_path),
                    output=str(report_path),
                )
            )

            self.assertTrue(report_path.exists())
            self.assertIn("FileGuard Security Analysis Report", report_path.read_text(encoding="utf-8"))

    @staticmethod
    def _write_config(root: Path, watch_dir: Path) -> Path:
        """Write a minimal valid FileGuard config to a temp directory."""
        config_path = root / "config.yaml"
        config_path.write_text(
            f"""
fileguard:
  watch_dirs:
    - "{watch_dir.as_posix()}"
  exclude_patterns: []
  analyzers:
    sensitive_path: {{enabled: true, policies: []}}
    entropy: {{enabled: true}}
    frequency: {{enabled: true, thresholds: {{created: 20, deleted: 15, modified: 30, moved: 25}}}}
    honeypot: {{enabled: true, filename_templates: []}}
    hash_diff: {{enabled: true}}
    fuzzy_hash: {{enabled: true}}
  scoring:
    levels:
      low: [0, 3.0]
      medium: [3.0, 5.0]
      high: [5.0, 7.0]
      critical: [7.0, 10.0]
  snapshot:
    enabled: true
    backup_files: true
    max_file_size_mb: 5
    backup_dir: ".fileguard/backups"
    baseline_file: ".fileguard/baseline.json"
  output:
    log_file: "{(root / 'events.jsonl').as_posix()}"
    report_file: "{(root / 'report.html').as_posix()}"
    dashboard_refresh_ms: 500
  api:
    host: "127.0.0.1"
    port: 8000
    cors_origins: []
  general:
    debounce_ms: 200
    max_queue_size: 10000
""",
            encoding="utf-8",
        )
        return config_path


if __name__ == "__main__":
    unittest.main()
