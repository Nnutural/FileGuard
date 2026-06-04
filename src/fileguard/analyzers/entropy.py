# -*- coding: utf-8 -*-
"""Entropy-based file content analyzer."""

from __future__ import annotations

import logging
import math
from collections import Counter
from pathlib import Path

from fileguard.analyzers.base import BaseAnalyzer
from fileguard.models import AnalysisSignal, FileEvent

logger = logging.getLogger(__name__)


def _clamp_score(value: float) -> float:
    """Clamp an analyzer score to the common 0.0 to 10.0 range."""
    return max(0.0, min(10.0, value))


class EntropyAnalyzer(BaseAnalyzer):
    """Detect high-entropy created or modified files."""

    _SUPPORTED_EVENTS = {"created", "modified"}

    @property
    def name(self) -> str:
        """Return the analyzer display name."""
        return "EntropyAnalyzer"

    @staticmethod
    def calculate_entropy(file_path: str | Path, block_size: int = 8192) -> float:
        """Calculate Shannon entropy for a file in the range 0.0 to 8.0."""
        path = Path(file_path)
        byte_counts: Counter[int] = Counter()
        total_bytes = 0

        with path.open("rb") as f:
            while True:
                chunk = f.read(block_size)
                if not chunk:
                    break
                byte_counts.update(chunk)
                total_bytes += len(chunk)

        if total_bytes == 0:
            return 0.0

        entropy = 0.0
        for count in byte_counts.values():
            probability = count / total_bytes
            if probability > 0:
                entropy -= probability * math.log2(probability)

        return entropy

    def analyze(self, event: FileEvent) -> AnalysisSignal | None:
        """Analyze a file event and return an entropy anomaly signal if needed."""
        if event.event_type not in self._SUPPORTED_EVENTS:
            return None
        if event.is_directory:
            logger.debug("Skipping directory event for entropy analysis: %s", event.src_path)
            return None

        path = Path(event.src_path)
        extension = path.suffix.lower()
        high_entropy_extensions = {
            str(ext).lower() for ext in self.config.get("high_entropy_extensions", [])
        }
        if extension in high_entropy_extensions:
            logger.debug("Skipping naturally high-entropy extension: %s", path)
            return None

        if not path.exists():
            logger.debug("Skipping missing file during entropy analysis: %s", path)
            return None
        if not path.is_file():
            logger.debug("Skipping non-file path during entropy analysis: %s", path)
            return None

        try:
            file_size = path.stat().st_size
            entropy = self.calculate_entropy(path)
        except PermissionError as exc:
            logger.warning("Unable to read file for entropy analysis: %s (%s)", path, exc)
            return None
        except OSError as exc:
            logger.warning("Failed to inspect file for entropy analysis: %s (%s)", path, exc)
            return None

        threshold = float(self.config.get("threshold", 6.5))
        if entropy <= threshold:
            return None

        denominator = max(0.000001, 8.0 - threshold)
        value = _clamp_score(6.0 + (entropy - threshold) / denominator * 4.0)

        evidence = {
            "path": str(path.resolve()),
            "entropy": entropy,
            "threshold": threshold,
            "extension": extension,
            "file_size": file_size,
        }
        logger.info("High entropy file detected: %s entropy=%.3f", path, entropy)
        return self.create_signal("entropy_anomaly", value, evidence)
