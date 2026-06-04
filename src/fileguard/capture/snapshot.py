# -*- coding: utf-8 -*-
"""Snapshot baseline and restore management."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from fileguard.analyzers.entropy import EntropyAnalyzer
from fileguard.analyzers.hash_diff import HashDiffChecker
from fileguard.models import FileSnapshot

logger = logging.getLogger(__name__)


class SnapshotManager:
    """Build file baselines, optionally back up content, and restore from them."""

    def __init__(self, config: dict) -> None:
        """Initialize the snapshot manager with the snapshot config section."""
        self.config = config
        self.baseline: dict[str, FileSnapshot] = {}

    def build_baseline(self, target_dir: str) -> dict[str, FileSnapshot]:
        """Scan a target directory and build a JSON-serializable baseline."""
        root = Path(target_dir).resolve()
        if not root.exists():
            raise FileNotFoundError(f"Snapshot target directory does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Snapshot target is not a directory: {root}")

        backup_dir = self._resolve_config_path("backup_dir", root)
        baseline_file = self._resolve_config_path("baseline_file", root)
        backup_files = bool(self.config.get("backup_files", True))
        max_file_size = int(float(self.config.get("max_file_size_mb", 50)) * 1024 * 1024)

        self.baseline = {}
        if backup_files:
            backup_dir.mkdir(parents=True, exist_ok=True)
        baseline_file.parent.mkdir(parents=True, exist_ok=True)

        for file_path in sorted(path for path in root.rglob("*") if path.is_file()):
            resolved = file_path.resolve()
            if self._is_internal_path(resolved, root, backup_dir, baseline_file):
                continue

            try:
                size = resolved.stat().st_size
                if size > max_file_size:
                    logger.info("Skipping large file in snapshot: %s", resolved)
                    continue

                sha256 = HashDiffChecker.compute_sha256(resolved)
                entropy = EntropyAnalyzer.calculate_entropy(resolved)
                backup_path: Path | None = None
                if backup_files:
                    backup_path = backup_dir / resolved.relative_to(root)
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(resolved, backup_path)

                snapshot = FileSnapshot(
                    path=str(resolved),
                    sha256=sha256,
                    size=size,
                    entropy=entropy,
                    snapshot_time=datetime.now(),
                    content_backup_path=str(backup_path.resolve()) if backup_path else None,
                )
                self.baseline[str(resolved)] = snapshot
            except OSError as exc:
                logger.warning("Failed to snapshot file: %s (%s)", resolved, exc)

        payload = {
            "created_at": datetime.now().isoformat(),
            "target_dir": str(root),
            "files": [snapshot.to_dict() for snapshot in self.baseline.values()],
        }
        baseline_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("Snapshot baseline written: %s (%d files)", baseline_file, len(self.baseline))
        return self.baseline

    def restore(self, snapshot_path: str, target_dir: str) -> dict[str, bool]:
        """Restore files from a snapshot's backup paths and verify SHA-256."""
        snapshot_file = Path(snapshot_path).resolve()
        target_root = Path(target_dir).resolve()
        target_root.mkdir(parents=True, exist_ok=True)

        payload = json.loads(snapshot_file.read_text(encoding="utf-8"))
        files = self._extract_snapshot_items(payload)
        original_root = Path(payload.get("target_dir", target_root)).resolve()

        results: dict[str, bool] = {}
        for item in files:
            source_path = Path(str(item.get("path", "")))
            backup_raw = item.get("content_backup_path")
            if not backup_raw:
                results[str(source_path)] = False
                continue

            backup_path = Path(str(backup_raw)).resolve()
            destination = self._restore_destination(source_path, original_root, target_root)
            try:
                if not backup_path.is_file():
                    results[str(destination)] = False
                    continue

                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_path, destination)
                restored_hash = HashDiffChecker.compute_sha256(destination)
                results[str(destination)] = restored_hash == str(item.get("sha256", ""))
            except OSError as exc:
                logger.warning("Failed to restore file: %s (%s)", destination, exc)
                results[str(destination)] = False

        logger.info(
            "Restore completed from %s: %d/%d verified",
            snapshot_file,
            sum(1 for ok in results.values() if ok),
            len(results),
        )
        return results

    def _resolve_config_path(self, key: str, root: Path) -> Path:
        """Resolve a config path relative to the snapshot target directory."""
        raw_value = self.config.get(key)
        default = ".fileguard/backups" if key == "backup_dir" else ".fileguard/baseline.json"
        path = Path(str(raw_value or default))
        if not path.is_absolute():
            path = root / path
        return path.resolve()

    @staticmethod
    def _extract_snapshot_items(payload: Any) -> list[dict[str, Any]]:
        """Extract snapshot records from supported baseline JSON shapes."""
        if isinstance(payload, dict) and isinstance(payload.get("files"), list):
            return [item for item in payload["files"] if isinstance(item, dict)]
        if isinstance(payload, dict):
            return [item for item in payload.values() if isinstance(item, dict)]
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        raise ValueError("Unsupported snapshot file format")

    @staticmethod
    def _is_internal_path(path: Path, root: Path, backup_dir: Path, baseline_file: Path) -> bool:
        """Return True for FileGuard metadata paths that should not be snapshotted."""
        try:
            relative = path.relative_to(root)
        except ValueError:
            return False

        if ".fileguard" in relative.parts:
            return True
        try:
            path.relative_to(backup_dir)
        except ValueError:
            in_backup_dir = False
        else:
            in_backup_dir = True
        if in_backup_dir:
            return True
        return path == baseline_file

    @staticmethod
    def _restore_destination(source_path: Path, original_root: Path, target_root: Path) -> Path:
        """Map a snapshot source path into the requested restore root."""
        try:
            relative = source_path.resolve().relative_to(original_root)
        except (OSError, ValueError):
            relative = Path(source_path.name)
        return target_root / relative
