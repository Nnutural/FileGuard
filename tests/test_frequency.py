# -*- coding: utf-8 -*-
"""Unit tests for FrequencyAnalyzer."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from fileguard.analyzers.frequency import FrequencyAnalyzer
from fileguard.models import FileEvent


class TestFrequencyAnalyzer(unittest.TestCase):
    """Test sliding-window event frequency analysis."""

    def setUp(self) -> None:
        """Initialize a frequency analyzer with small thresholds."""
        self.base_time = datetime(2026, 1, 1, 12, 0, 0)
        self.analyzer = FrequencyAnalyzer(
            {
                "enabled": True,
                "weight": 2.5,
                "window_seconds": 10,
                "thresholds": {
                    "created": 3,
                    "modified": 2,
                    "deleted": 2,
                    "moved": 2,
                },
            }
        )

    def _event(self, event_type: str, seconds: int) -> FileEvent:
        """Create a file event at an offset from the test base time."""
        return FileEvent(
            timestamp=self.base_time + timedelta(seconds=seconds),
            event_type=event_type,
            src_path=f"file_{event_type}_{seconds}.txt",
            is_directory=False,
        )

    def test_single_event_does_not_trigger(self) -> None:
        """A single event should be below all thresholds."""
        signal = self.analyzer.analyze(self._event("modified", 0))

        self.assertIsNone(signal)

    def test_below_threshold_does_not_trigger(self) -> None:
        """Counts below or equal to threshold should not trigger."""
        signals = [
            self.analyzer.analyze(self._event("created", 0)),
            self.analyzer.analyze(self._event("created", 1)),
            self.analyzer.analyze(self._event("created", 2)),
        ]

        self.assertEqual(signals, [None, None, None])

    def test_above_threshold_triggers(self) -> None:
        """A per-type count above threshold should produce a freq_spike signal."""
        for offset in range(3):
            self.assertIsNone(self.analyzer.analyze(self._event("created", offset)))

        signal = self.analyzer.analyze(self._event("created", 3))

        self.assertIsNotNone(signal)
        self.assertEqual(signal.signal_type, "freq_spike")
        self.assertEqual(signal.evidence["event_type"], "created")
        self.assertEqual(signal.evidence["count"], 4)
        self.assertEqual(signal.evidence["threshold"], 3)
        self.assertEqual(signal.evidence["buffer_size"], 4)

    def test_events_outside_window_are_purged(self) -> None:
        """Expired events should not count toward the current window."""
        analyzer = FrequencyAnalyzer(
            {
                "window_seconds": 5,
                "thresholds": {"created": 1},
            }
        )

        self.assertIsNone(analyzer.analyze(self._event("created", 0)))
        signal = analyzer.analyze(self._event("created", 10))

        self.assertIsNone(signal)
        self.assertEqual(len(analyzer._event_buffer), 1)

    def test_different_event_types_are_counted_separately(self) -> None:
        """Total event volume alone should not trigger another type's threshold."""
        self.assertIsNone(self.analyzer.analyze(self._event("created", 0)))
        self.assertIsNone(self.analyzer.analyze(self._event("created", 1)))
        self.assertIsNone(self.analyzer.analyze(self._event("deleted", 2)))
        self.assertIsNone(self.analyzer.analyze(self._event("deleted", 3)))

        signal = self.analyzer.analyze(self._event("deleted", 4))

        self.assertIsNotNone(signal)
        self.assertEqual(signal.signal_type, "freq_spike")
        self.assertEqual(signal.evidence["event_type"], "deleted")
        self.assertEqual(signal.evidence["count"], 3)


if __name__ == "__main__":
    unittest.main()
