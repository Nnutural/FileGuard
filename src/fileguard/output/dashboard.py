# -*- coding: utf-8 -*-
"""Rich-based CLI dashboard for recent FileGuard assessments."""

from __future__ import annotations

import logging
from collections import Counter, deque
from typing import Any

from fileguard.models import RiskAssessment

logger = logging.getLogger(__name__)


class Dashboard:
    """A lightweight live terminal dashboard."""

    def __init__(self, config: dict) -> None:
        """Initialize dashboard state."""
        self.config = config
        self._assessments: deque[RiskAssessment] = deque(maxlen=int(config.get("max_rows", 20)))
        self._level_counts: Counter[str] = Counter()
        self._live: Any | None = None
        self._started = False

    def start(self) -> None:
        """Start the rich Live context if rich is available."""
        if self._started:
            return
        try:
            from rich.live import Live
        except ImportError:
            logger.info("rich is not installed; CLI dashboard disabled.")
            self._started = True
            return

        refresh_ms = int(self.config.get("dashboard_refresh_ms", 500))
        refresh_per_second = max(1.0, 1000.0 / max(1, refresh_ms))
        self._live = Live(
            self._render(),
            refresh_per_second=refresh_per_second,
            transient=False,
        )
        self._live.start()
        self._started = True
        logger.info("CLI dashboard started.")

    def stop(self) -> None:
        """Stop the rich Live context."""
        if self._live is not None:
            self._live.stop()
            self._live = None
        self._started = False
        logger.info("CLI dashboard stopped.")

    def update(self, assessment: RiskAssessment) -> None:
        """Record a new assessment and refresh the live dashboard."""
        self._assessments.appendleft(assessment)
        self._level_counts[assessment.level] += 1

        if self._live is not None:
            self._live.update(self._render())
        else:
            logger.info(
                "Assessment: level=%s score=%.2f event=%s path=%s",
                assessment.level,
                assessment.score,
                assessment.event.event_type,
                assessment.event.src_path,
            )

    def _render(self) -> Any:
        """Build the rich renderable for the current dashboard state."""
        try:
            from rich.console import Group
            from rich.panel import Panel
            from rich.table import Table
        except ImportError:
            return "FileGuard dashboard unavailable: rich is not installed."

        summary = Table.grid(expand=True)
        summary.add_column(justify="center")
        summary.add_column(justify="center")
        summary.add_column(justify="center")
        summary.add_column(justify="center")
        summary.add_column(justify="center")
        summary.add_row(
            f"Total: {sum(self._level_counts.values())}",
            f"LOW: {self._level_counts['LOW']}",
            f"MEDIUM: {self._level_counts['MEDIUM']}",
            f"HIGH: {self._level_counts['HIGH']}",
            f"CRITICAL: {self._level_counts['CRITICAL']}",
        )

        events = Table(title="Recent FileGuard Assessments", expand=True)
        events.add_column("Time", no_wrap=True)
        events.add_column("Level", no_wrap=True)
        events.add_column("Score", justify="right", no_wrap=True)
        events.add_column("Event", no_wrap=True)
        events.add_column("Path")
        events.add_column("Signals")

        for assessment in self._assessments:
            signal_names = ", ".join(signal.signal_type for signal in assessment.signals) or "-"
            events.add_row(
                assessment.timestamp.strftime("%H:%M:%S"),
                assessment.level,
                f"{assessment.score:.2f}",
                assessment.event.event_type,
                assessment.event.src_path,
                signal_names,
            )

        return Group(
            Panel(summary, title="FileGuard Status"),
            events,
        )
