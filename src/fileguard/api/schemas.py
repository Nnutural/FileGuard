# -*- coding: utf-8 -*-
"""FastAPI response models for FileGuard."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class LevelCounts(BaseModel):
    """Risk-level count summary."""

    LOW: int = 0
    MEDIUM: int = 0
    HIGH: int = 0
    CRITICAL: int = 0


class StatusResponse(BaseModel):
    """Current monitor status."""

    running: bool
    watch_dirs: list[str]
    uptime_seconds: float
    events_processed: int
    queue_size: int
    events_total: int
    alerts_total: int
    highest_level: str
    last_event_time: str | None = None
    last_alert_time: str | None = None
    analyzers_enabled: int = 0
    snapshot_available: bool = False
    report_available: bool = False


class SignalItem(BaseModel):
    """One analyzer signal in an alert response."""

    analyzer_name: str
    signal_type: str
    value: float
    weight: float
    evidence: dict[str, Any]
    timestamp: str


class AlertItem(BaseModel):
    """One alert row."""

    timestamp: str
    event_type: str
    src_path: str
    dest_path: str | None = None
    score: float
    level: str
    analyzers: list[str]
    signal_types: list[str] = []
    signals: list[SignalItem] = []
    escalated: bool = False
    escalation_reason: str | None = None


class AlertsResponse(BaseModel):
    """Alert list response."""

    total: int
    alerts: list[AlertItem]
    by_level: LevelCounts = LevelCounts()


class EventItem(BaseModel):
    """One file event row."""

    timestamp: str
    event_type: str
    src_path: str
    dest_path: str | None = None
    file_size: int | None = None
    is_directory: bool = False
    score: float | None = None
    level: str | None = None
    signals_count: int = 0


class EventsResponse(BaseModel):
    """Recent file event list response."""

    total: int
    events: list[EventItem]


class AnalyzerItem(BaseModel):
    """Analyzer status summary."""

    name: str
    enabled: bool
    weight: float
    signals_total: int = 0
    last_triggered_at: str | None = None


class AnalyzersResponse(BaseModel):
    """Analyzer status response."""

    total: int
    items: list[AnalyzerItem]


class IncrementalSnapshotItem(BaseModel):
    """One runtime snapshot delta."""

    path: str
    old_hash: str | None = None
    new_hash: str | None = None
    old_entropy: float | None = None
    new_entropy: float | None = None
    timestamp: str
    event_type: str


class SnapshotsResponse(BaseModel):
    """Snapshot status response."""

    enabled: bool
    baseline_file: str | None = None
    backup_dir: str | None = None
    files_total: int = 0
    last_snapshot_time: str | None = None
    last_restore_verified: bool | None = None
    incremental_total: int = 0
    incremental_records: list[IncrementalSnapshotItem] = []
    auto_restore_actions: list[dict[str, Any]] = []


class ReportStatusResponse(BaseModel):
    """Report status or generation response."""

    ok: bool = True
    report_file: str
    available: bool = False
    generated_at: str | None = None
    events_total: int = 0
    alerts_total: int = 0
    error: str | None = None
