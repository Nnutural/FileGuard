# -*- coding: utf-8 -*-
"""Snapshot baseline and restore management."""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from fileguard.analyzers.entropy import EntropyAnalyzer
from fileguard.analyzers.hash_diff import HashDiffChecker
from fileguard.models import FileEvent, FileSnapshot, RiskAssessment

logger = logging.getLogger(__name__)


@dataclass
class IncrementalSnapshotRecord:
    """Metadata-only record for a runtime file change."""

    path: str
    old_hash: str | None
    new_hash: str | None
    old_entropy: float | None
    new_entropy: float | None
    timestamp: datetime
    event_type: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "path": self.path,
            "old_hash": self.old_hash,
            "new_hash": self.new_hash,
            "old_entropy": self.old_entropy,
            "new_entropy": self.new_entropy,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
        }


class SnapshotManager:
    """Build file baselines, optionally back up content, and restore from them."""

    def __init__(self, config: dict) -> None:
        """Initialize the snapshot manager with the snapshot config section."""
        self.config = config
        self.baseline: dict[str, FileSnapshot] = {}
        self.last_baseline_file: Path | None = None
        self.last_backup_dir: Path | None = None
        self.last_target_dir: Path | None = None
        self.last_snapshot_time: datetime | None = None
        self.last_restore_verified: bool | None = None
        self.incremental_records: list[IncrementalSnapshotRecord] = []
        self.auto_restore_actions: list[dict[str, Any]] = []

    def build_baseline(self, target_dir: str) -> dict[str, FileSnapshot]:
        """Scan a target directory and build a JSON-serializable baseline."""
        root = Path(target_dir).resolve()
        if not root.exists():
            raise FileNotFoundError(f"Snapshot target directory does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Snapshot target is not a directory: {root}")

        backup_dir = self._resolve_config_path("backup_dir", root)
        baseline_file = self._resolve_config_path("baseline_file", root)
        self.last_backup_dir = backup_dir
        self.last_baseline_file = baseline_file
        self.last_target_dir = root
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
        self.last_snapshot_time = datetime.now()
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
        self.last_restore_verified = bool(results) and all(results.values())
        return results

    def update_incremental(self, event: FileEvent) -> IncrementalSnapshotRecord | None:
        """Record a metadata-only runtime snapshot delta for created/modified files."""
        if event.event_type not in {"created", "modified"} or event.is_directory:
            return None

        path = Path(event.src_path).resolve()
        if not path.is_file():
            return None

        old_snapshot = self.baseline.get(str(path))
        try:
            record = IncrementalSnapshotRecord(
                path=str(path),
                old_hash=old_snapshot.sha256 if old_snapshot else None,
                new_hash=HashDiffChecker.compute_sha256(path),
                old_entropy=old_snapshot.entropy if old_snapshot else None,
                new_entropy=EntropyAnalyzer.calculate_entropy(path),
                timestamp=datetime.now(),
                event_type=event.event_type,
            )
        except OSError as exc:
            logger.warning("Failed to update incremental snapshot for %s: %s", path, exc)
            return None

        self.incremental_records.append(record)
        self.incremental_records = self.incremental_records[-200:]
        self._append_incremental_record(record)
        return record

    def get_incremental_records(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent runtime snapshot deltas."""
        return [record.to_dict() for record in self.incremental_records[-limit:]]

    def get_status(self) -> dict[str, Any]:
        """Return snapshot state for API presentation."""
        return {
            "enabled": bool(self.config.get("enabled", True)),
            "baseline_file": str(self.last_baseline_file) if self.last_baseline_file else None,
            "backup_dir": str(self.last_backup_dir) if self.last_backup_dir else None,
            "files_total": len(self.baseline),
            "last_snapshot_time": self.last_snapshot_time.isoformat() if self.last_snapshot_time else None,
            "last_restore_verified": self.last_restore_verified,
            "incremental_total": len(self.incremental_records),
            "incremental_records": self.get_incremental_records(),
            "auto_restore_actions": list(self.auto_restore_actions[-20:]),
        }

    def auto_restore_if_needed(
        self,
        assessment: RiskAssessment,
        sandbox_root: str,
        enabled: bool = False,
        dry_run: bool = True,
    ) -> dict[str, Any] | None:
        """Optionally restore a CRITICAL sandbox file from this manager's baseline backup."""
        if not enabled or assessment.level != "CRITICAL":
            return None

        sandbox = Path(sandbox_root).resolve()
        target = Path(assessment.event.src_path).resolve()
        action: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "path": str(target),
            "dry_run": dry_run,
            "restored": False,
            "verified": False,
            "reason": "",
        }

        try:
            target.relative_to(sandbox)
        except ValueError:
            action["reason"] = "refused: target is outside experiments/sandbox"
            self.auto_restore_actions.append(action)
            return action

        snapshot = self.baseline.get(str(target))
        if snapshot is None or not snapshot.content_backup_path:
            action["reason"] = "no baseline backup for target"
            self.auto_restore_actions.append(action)
            return action

        backup = Path(snapshot.content_backup_path).resolve()
        if not backup.is_file():
            action["reason"] = "baseline backup file is missing"
            self.auto_restore_actions.append(action)
            return action

        if dry_run:
            action["reason"] = "dry-run candidate"
            self.auto_restore_actions.append(action)
            return action

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, target)
            action["restored"] = True
            action["verified"] = HashDiffChecker.compute_sha256(target) == snapshot.sha256
            action["reason"] = "restored from baseline backup"
        except OSError as exc:
            action["reason"] = f"restore failed: {exc}"
            logger.warning("Auto-restore failed for %s: %s", target, exc)
        self.auto_restore_actions.append(action)
        return action

    def _resolve_config_path(self, key: str, root: Path) -> Path:
        """Resolve a config path relative to the snapshot target directory."""
        raw_value = self.config.get(key)
        default = ".fileguard/backups" if key == "backup_dir" else ".fileguard/baseline.json"
        path = Path(str(raw_value or default))
        if not path.is_absolute():
            path = root / path
        return path.resolve()

    def _append_incremental_record(self, record: IncrementalSnapshotRecord) -> None:
        """Append a runtime snapshot record to the configured JSONL file."""
        raw_path = self.config.get("incremental_file", ".fileguard/incremental_snapshots.jsonl")
        base = self.last_target_dir or Path.cwd()
        path = Path(str(raw_path))
        if not path.is_absolute():
            path = base / path
        path = path.resolve()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.warning("Failed to write incremental snapshot record: %s", exc)

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
