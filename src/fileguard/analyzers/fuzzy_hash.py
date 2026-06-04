# -*- coding: utf-8 -*-
"""Block-hash similarity analyzer."""

from __future__ import annotations

import hashlib
import logging
from collections import Counter
from pathlib import Path

from fileguard.analyzers.base import BaseAnalyzer
from fileguard.models import AnalysisSignal, FileEvent

logger = logging.getLogger(__name__)


def _clamp_score(value: float) -> float:
    """Clamp an analyzer score to the common 0.0 to 10.0 range."""
    return max(0.0, min(10.0, value))


class FuzzyHashAnalyzer(BaseAnalyzer):
    """Detect sharp content similarity drops with lightweight block hashes."""

    def __init__(self, config: dict) -> None:
        """Initialize the analyzer with an in-memory block-hash baseline."""
        super().__init__(config)
        self._block_baseline: dict[str, list[str]] = {}

    @property
    def name(self) -> str:
        """Return the analyzer display name."""
        return "FuzzyHashAnalyzer"

    def analyze(self, event: FileEvent) -> AnalysisSignal | None:
        """Compare current block hashes with the previous in-memory baseline."""
        if event.event_type != "modified":
            return None
        if event.is_directory:
            logger.debug("Skipping directory event for fuzzy hash analysis: %s", event.src_path)
            return None

        path = Path(event.src_path)
        if not path.exists():
            logger.debug("Skipping missing file during fuzzy hash analysis: %s", path)
            return None
        if not path.is_file():
            logger.debug("Skipping non-file path during fuzzy hash analysis: %s", path)
            return None

        block_size = int(self.config.get("block_size", 4096))
        try:
            new_blocks = self._compute_block_hashes(path, block_size)
        except PermissionError as exc:
            logger.warning("Unable to read file for fuzzy hash analysis: %s (%s)", path, exc)
            return None
        except OSError as exc:
            logger.warning("Failed to inspect file for fuzzy hash analysis: %s (%s)", path, exc)
            return None

        key = self._path_key(path)
        old_blocks = self._block_baseline.get(key)
        if old_blocks is None:
            self._block_baseline[key] = new_blocks
            return None

        similarity = self._calculate_similarity(old_blocks, new_blocks)
        threshold = float(self.config.get("similarity_threshold", 0.3))
        self._block_baseline[key] = new_blocks

        if similarity >= threshold:
            return None

        if threshold > 0:
            value = 6.0 + (threshold - similarity) / threshold * 4.0
        else:
            value = 10.0
        value = _clamp_score(value)

        evidence = {
            "path": str(path.resolve()),
            "similarity": similarity,
            "threshold": threshold,
            "old_block_count": len(old_blocks),
            "new_block_count": len(new_blocks),
        }
        logger.info(
            "File similarity dropped: %s similarity=%.3f threshold=%.3f",
            path,
            similarity,
            threshold,
        )
        return self.create_signal("similarity_drop", value, evidence)

    def _compute_block_hashes(self, file_path: Path, block_size: int) -> list[str]:
        """Compute MD5 hashes for each fixed-size file block."""
        safe_block_size = max(1, int(block_size))
        block_hashes: list[str] = []
        with file_path.open("rb") as f:
            while True:
                chunk = f.read(safe_block_size)
                if not chunk:
                    break
                block_hashes.append(hashlib.md5(chunk).hexdigest())
        return block_hashes

    def _calculate_similarity(self, old_blocks: list[str], new_blocks: list[str]) -> float:
        """Calculate multiset block overlap normalized by the larger block count."""
        max_count = max(len(old_blocks), len(new_blocks))
        if max_count == 0:
            return 1.0

        old_counter = Counter(old_blocks)
        new_counter = Counter(new_blocks)
        overlap = sum((old_counter & new_counter).values())
        return overlap / max_count

    @staticmethod
    def _path_key(path: Path) -> str:
        """Return a stable string key for the in-memory baseline map."""
        return str(path.resolve())
