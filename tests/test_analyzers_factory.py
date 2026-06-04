# -*- coding: utf-8 -*-
"""Unit tests for analyzer factory creation."""

from __future__ import annotations

import unittest

from fileguard.analyzers import create_analyzers
from fileguard.analyzers.entropy import EntropyAnalyzer
from fileguard.analyzers.frequency import FrequencyAnalyzer
from fileguard.analyzers.fuzzy_hash import FuzzyHashAnalyzer
from fileguard.analyzers.hash_diff import HashDiffChecker
from fileguard.analyzers.honeypot import HoneypotSentinel
from fileguard.analyzers.sensitive_path import SensitivePathAnalyzer
from fileguard.config import load_config


class TestAnalyzerFactory(unittest.TestCase):
    """Test that config.example.yaml creates all enabled analyzers."""

    def test_create_analyzers_from_example_config(self) -> None:
        """The factory should create six analyzers in a stable order."""
        config = load_config("config.example.yaml")

        analyzers = create_analyzers(config)

        self.assertEqual(len(analyzers), 6)
        self.assertEqual(
            [type(analyzer) for analyzer in analyzers],
            [
                SensitivePathAnalyzer,
                EntropyAnalyzer,
                FrequencyAnalyzer,
                HoneypotSentinel,
                HashDiffChecker,
                FuzzyHashAnalyzer,
            ],
        )
        self.assertEqual(
            [analyzer.name for analyzer in analyzers],
            [
                "SensitivePathAnalyzer",
                "EntropyAnalyzer",
                "FrequencyAnalyzer",
                "HoneypotSentinel",
                "HashDiffChecker",
                "FuzzyHashAnalyzer",
            ],
        )


if __name__ == "__main__":
    unittest.main()
