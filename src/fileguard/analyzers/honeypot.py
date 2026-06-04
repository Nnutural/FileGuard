# -*- coding: utf-8 -*-
"""Honeypot file sentinel analyzer."""

from __future__ import annotations

import logging
from pathlib import Path

from fileguard.analyzers.base import BaseAnalyzer
from fileguard.models import AnalysisSignal, FileEvent

logger = logging.getLogger(__name__)


class HoneypotSentinel(BaseAnalyzer):
    """Deploy and monitor canary files used as high-confidence tripwires."""

    def __init__(self, config: dict) -> None:
        """Initialize the sentinel with an in-memory honeypot path set."""
        super().__init__(config)
        self._honeypot_paths: set[str] = set()

    @property
    def name(self) -> str:
        """Return the analyzer display name."""
        return "HoneypotSentinel"

    def deploy_honeypots(self, target_dir: str) -> list[str]:
        """Create configured honeypot files in a target directory idempotently."""
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        templates = [
            str(name)
            for name in self.config.get("filename_templates", [])
            if str(name).strip()
        ]
        if not templates:
            templates = ["~$fileguard_honeypot.tmp"]

        deploy_count = int(self.config.get("deploy_count", len(templates)))
        selected_templates = templates[: max(0, min(deploy_count, len(templates)))]
        deployed_paths: list[str] = []

        for filename in selected_templates:
            honeypot_path = target_path / filename
            try:
                if honeypot_path.exists() and not honeypot_path.is_file():
                    logger.warning("Skipping non-file honeypot path: %s", honeypot_path)
                    continue
                if not honeypot_path.exists():
                    honeypot_path.write_text(
                        self._honeypot_content(filename),
                        encoding="utf-8",
                    )
                resolved = str(honeypot_path.resolve())
                self._honeypot_paths.add(resolved)
                deployed_paths.append(resolved)
            except OSError as exc:
                logger.warning("Failed to deploy honeypot file: %s (%s)", honeypot_path, exc)

        return deployed_paths

    def analyze(self, event: FileEvent) -> AnalysisSignal | None:
        """Return a critical signal when an event touches a honeypot path."""
        candidates = [event.src_path]
        if event.dest_path:
            candidates.append(event.dest_path)

        for candidate in candidates:
            resolved = str(Path(candidate).resolve())
            if resolved not in self._honeypot_paths:
                continue

            evidence = {
                "path": resolved,
                "event_type": event.event_type,
                "honeypot_path": resolved,
            }
            logger.warning("Honeypot triggered: event_type=%s path=%s", event.event_type, resolved)
            return self.create_signal("honeypot_triggered", 10.0, evidence)

        return None

    @staticmethod
    def _honeypot_content(filename: str) -> str:
        """Return low-entropy text content for a honeypot file."""
        return (
            "FileGuard honeypot document\n"
            f"Name: {filename}\n"
            "This controlled file should not be modified by normal workflows.\n"
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        )
