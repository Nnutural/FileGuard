# -*- coding: utf-8 -*-
"""Sliding-window file event frequency analyzer."""

from __future__ import annotations

import logging
from collections import Counter, deque
from datetime import timedelta

from fileguard.analyzers.base import BaseAnalyzer
from fileguard.models import AnalysisSignal, FileEvent

logger = logging.getLogger(__name__)


def _clamp_score(value: float) -> float:
    """Clamp an analyzer score to the common 0.0 to 10.0 range."""
    return max(0.0, min(10.0, value))


class FrequencyAnalyzer(BaseAnalyzer):
    """Detect spikes in per-event-type activity within a sliding window."""

    def __init__(self, config: dict) -> None:
        """Initialize the frequency analyzer with an in-memory event buffer."""
        super().__init__(config)
        self._event_buffer: deque[FileEvent] = deque()

    @property
    def name(self) -> str:
        """Return the analyzer display name."""
        return "FrequencyAnalyzer"

    def analyze(self, event: FileEvent) -> AnalysisSignal | None:
        """Add an event to the window and return a spike signal when exceeded."""
        self._event_buffer.append(event)

        window_seconds = float(self.config.get("window_seconds", 10))
        self._purge_expired_events(event, window_seconds)

        counts = Counter(item.event_type for item in self._event_buffer)
        thresholds = self.config.get("thresholds", {})
        threshold_raw = thresholds.get(event.event_type)
        if threshold_raw is None:
            return None

        threshold = int(threshold_raw)
        count = counts[event.event_type]
        if count <= threshold:
            return None

        if threshold > 0:
            value = 5.0 + (count - threshold) / threshold * 5.0
        else:
            value = 10.0
        value = _clamp_score(value)

        evidence = {
            "event_type": event.event_type,
            "count": count,
            "threshold": threshold,
            "window_seconds": window_seconds,
            "buffer_size": len(self._event_buffer),
        }
        logger.info(
            "Frequency spike detected: event_type=%s count=%d threshold=%d",
            event.event_type,
            count,
            threshold,
        )
        return self.create_signal("freq_spike", value, evidence)

    def _purge_expired_events(self, current_event: FileEvent, window_seconds: float) -> None:
        """Remove events outside the configured sliding window."""
        cutoff = current_event.timestamp - timedelta(seconds=window_seconds)
        self._event_buffer = deque(
            item for item in self._event_buffer if item.timestamp >= cutoff
        )
