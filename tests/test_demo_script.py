# -*- coding: utf-8 -*-
"""Tests for the safe demo script."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class TestDemoScript(unittest.TestCase):
    """Run the demo script and verify declared artifacts."""

    def test_demo_script_generates_summary(self) -> None:
        result = subprocess.run(
            [sys.executable, "experiments/run_demo.py", "--config", "config.example.yaml"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        summary_path = Path("experiments/sandbox/outputs/demo_summary.json")
        self.assertTrue(summary_path.exists())
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertGreater(summary["events_total"], 0)
        self.assertIn("escalations_total", summary)
        self.assertTrue(Path("experiments/sandbox/outputs/artifact_index.md").exists())


if __name__ == "__main__":
    unittest.main()
