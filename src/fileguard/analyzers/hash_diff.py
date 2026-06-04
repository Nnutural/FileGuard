# -*- coding: utf-8 -*-
"""SHA-256 hash difference analyzer."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from fileguard.analyzers.base import BaseAnalyzer
from fileguard.models import AnalysisSignal, FileEvent

logger = logging.getLogger(__name__)


def _clamp_score(value: float) -> float:
    """Clamp an analyzer score to the common 0.0 to 10.0 range."""
    return max(0.0, min(10.0, value))


class HashDiffChecker(BaseAnalyzer):
    """Track lightweight in-memory SHA-256 baselines for file changes."""

    _SUPPORTED_EVENTS = {"created", "modified"}

    def __init__(self, config: dict) -> None:
        """Initialize the checker with optional config-provided baseline hashes."""
        super().__init__(config)
        self._known_hashes: dict[str, str] = {}
        baseline_hashes = config.get("baseline_hashes", {})
        if isinstance(baseline_hashes, dict):
            for raw_path, raw_hash in baseline_hashes.items():
                self._known_hashes[self._path_key(Path(str(raw_path)))] = str(raw_hash)

    @property
    def name(self) -> str:
        """Return the analyzer display name."""
        return "HashDiffChecker"

    @staticmethod
    def compute_sha256(file_path: str | Path, block_size: int = 65536) -> str:
        """Calculate a file's SHA-256 digest using chunked reads."""
        path = Path(file_path)
        sha256 = hashlib.sha256()
        with path.open("rb") as f:
            while True:
                chunk = f.read(block_size)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()

    def analyze(self, event: FileEvent) -> AnalysisSignal | None:
        """Compare the current file hash with the in-memory baseline."""
        if event.event_type not in self._SUPPORTED_EVENTS:
            return None
        if event.is_directory:
            logger.debug("Skipping directory event for hash analysis: %s", event.src_path)
            return None

        path = Path(event.src_path)
        if not path.exists():
            logger.debug("Skipping missing file during hash analysis: %s", path)
            return None
        if not path.is_file():
            logger.debug("Skipping non-file path during hash analysis: %s", path)
            return None

        try:
            file_size = path.stat().st_size
            new_hash = self.compute_sha256(path)
        except PermissionError as exc:
            logger.warning("Unable to read file for hash analysis: %s (%s)", path, exc)
            return None
        except OSError as exc:
            logger.warning("Failed to inspect file for hash analysis: %s (%s)", path, exc)
            return None

        key = self._path_key(path)
        old_hash = self._known_hashes.get(key)
        if old_hash is None:
            self._known_hashes[key] = new_hash
            return None
        if old_hash == new_hash:
            return None

        self._known_hashes[key] = new_hash
        evidence = {
            "path": str(path.resolve()),
            "old_hash": old_hash,
            "new_hash": new_hash,
            "file_size": file_size,
        }
        logger.info("File hash changed: %s", path)
        return self.create_signal("hash_changed", _clamp_score(5.0), evidence)

    @staticmethod
    def _path_key(path: Path) -> str:
        """Return a stable string key for the in-memory baseline map."""
        return str(path.resolve())
