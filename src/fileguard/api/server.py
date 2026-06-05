# -*- coding: utf-8 -*-
"""FastAPI application and routes for FileGuard."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from fileguard.api.schemas import (
    AlertItem,
    AlertsResponse,
    AnalyzerItem,
    AnalyzersResponse,
    EventItem,
    EventsResponse,
    LevelCounts,
    ReportStatusResponse,
    SignalItem,
    SnapshotsResponse,
    StatusResponse,
)
from fileguard.capture.snapshot import SnapshotManager
from fileguard.models import AnalysisSignal, FileEvent, RiskAssessment
from fileguard.output.report import ReportGenerator
from fileguard.scoring.alert import AlertManager

logger = logging.getLogger(__name__)

_LEVEL_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


@dataclass
class ApiRuntimeState:
    """Runtime state exposed through the API layer."""

    running: bool = False
    watch_dirs: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    events_processed: int = 0
    queue_size: int = 0
    recent_events: list[FileEvent] = field(default_factory=list)
    recent_assessments: list[RiskAssessment] = field(default_factory=list)
    alert_manager: AlertManager | None = None
    analyzers: list[Any] = field(default_factory=list)
    snapshot_manager: SnapshotManager | None = None
    log_file: str = ".fileguard/events.jsonl"
    report_file: str = ".fileguard/report.html"
    template_path: str = "templates/report.html"
    stream_events: list[dict[str, Any]] = field(default_factory=list)

    def record_event(self, event: FileEvent, queue_size: int = 0) -> None:
        """Record a processed event for API retrieval."""
        self.events_processed += 1
        self.queue_size = queue_size
        self.recent_events.append(event)
        self.recent_events = self.recent_events[-200:]
        self._push_stream("event", _event_to_item(event).model_dump())

    def record_assessment(self, assessment: RiskAssessment, queue_size: int = 0) -> None:
        """Record a processed assessment with event and optional alert details."""
        self.events_processed += 1
        self.queue_size = queue_size
        self.recent_events.append(assessment.event)
        self.recent_events = self.recent_events[-200:]
        self.recent_assessments.append(assessment)
        self.recent_assessments = self.recent_assessments[-200:]
        self._push_stream("event", _event_to_item(assessment.event, assessment).model_dump())
        if assessment.signals:
            self._push_stream("alert", _assessment_to_alert_item(assessment, self.alert_manager).model_dump())

    def report_available(self) -> bool:
        """Return True when the configured report file exists."""
        return Path(self.report_file).exists()

    def _push_stream(self, event_type: str, data: dict[str, Any]) -> None:
        """Append a lightweight event-stream item."""
        self.stream_events.append(
            {
                "id": len(self.stream_events) + 1,
                "event": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self.stream_events = self.stream_events[-500:]


def create_app(
    cors_origins: list[str] | None = None,
    runtime_state: ApiRuntimeState | None = None,
) -> FastAPI:
    """Create and return a configured FastAPI application."""
    app = FastAPI(
        title="FileGuard API",
        version="0.1.0",
        description="File security risk sensing and protection verification API.",
    )
    app.state.runtime_state = runtime_state or ApiRuntimeState()

    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/api/status", response_model=StatusResponse)
    async def get_status() -> StatusResponse:
        """Return current monitor status."""
        return _status_response(app.state.runtime_state)

    @app.get("/api/alerts", response_model=AlertsResponse)
    async def get_alerts() -> AlertsResponse:
        """Return recorded alerts from AlertManager."""
        state: ApiRuntimeState = app.state.runtime_state
        timeline = state.alert_manager.get_timeline() if state.alert_manager else []
        alerts = [_assessment_to_alert_item(assessment, state.alert_manager) for assessment in timeline]
        return AlertsResponse(total=len(alerts), alerts=alerts, by_level=_level_counts(timeline))

    @app.get("/api/events", response_model=EventsResponse)
    async def get_events() -> EventsResponse:
        """Return recent file events recorded by the runtime state."""
        state: ApiRuntimeState = app.state.runtime_state
        events = [
            _event_to_item(assessment.event, assessment)
            for assessment in reversed(state.recent_assessments)
        ]
        if not events:
            events = [_event_to_item(event) for event in reversed(state.recent_events)]
        return EventsResponse(total=len(events), events=events)

    @app.get("/api/analyzers", response_model=AnalyzersResponse)
    async def get_analyzers() -> AnalyzersResponse:
        """Return analyzer status and trigger counts."""
        state: ApiRuntimeState = app.state.runtime_state
        items = _analyzer_items(state)
        return AnalyzersResponse(total=len(items), items=items)

    @app.get("/api/snapshots", response_model=SnapshotsResponse)
    async def get_snapshots() -> SnapshotsResponse:
        """Return snapshot and restore status."""
        state: ApiRuntimeState = app.state.runtime_state
        if state.snapshot_manager is None:
            return SnapshotsResponse(enabled=False)
        return SnapshotsResponse(**state.snapshot_manager.get_status())

    @app.get("/api/reports", response_model=ReportStatusResponse)
    async def get_reports() -> ReportStatusResponse:
        """Return report file status."""
        return _report_status(app.state.runtime_state)

    @app.post("/api/reports", response_model=ReportStatusResponse)
    async def post_reports() -> ReportStatusResponse:
        """Generate an HTML report from the current timeline or JSONL log."""
        state: ApiRuntimeState = app.state.runtime_state
        try:
            timeline = _report_timeline(state)
            report_path = _safe_report_path(state.report_file)
            generator = ReportGenerator(state.template_path, str(report_path))
            generator.generate(timeline)
            return _report_status(state, ok=True, generated_at=datetime.now().isoformat())
        except Exception as exc:
            logger.warning("Report generation failed: %s", exc)
            raise HTTPException(status_code=400, detail={"ok": False, "error": str(exc)}) from exc

    @app.get("/api/stream")
    async def stream(once: bool = False) -> StreamingResponse:
        """Stream status, event, and alert changes using Server-Sent Events."""

        async def event_generator() -> Iterable[str]:
            state: ApiRuntimeState = app.state.runtime_state
            last_id = 0
            yield _sse("status", _status_response(state).model_dump(), 0)
            if once:
                return
            while True:
                new_items = [item for item in state.stream_events if int(item["id"]) > last_id]
                for item in new_items:
                    last_id = int(item["id"])
                    yield _sse(str(item["event"]), item["data"], last_id)
                if not new_items:
                    yield _sse("heartbeat", {"ok": True, "timestamp": datetime.now().isoformat()}, last_id)
                await asyncio.sleep(1.0)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return app


def _status_response(state: ApiRuntimeState) -> StatusResponse:
    """Build the status DTO."""
    uptime = (datetime.now() - state.started_at).total_seconds()
    timeline = state.alert_manager.get_timeline() if state.alert_manager else []
    highest = _highest_level(assessment.level for assessment in timeline)
    return StatusResponse(
        running=state.running,
        watch_dirs=state.watch_dirs,
        uptime_seconds=uptime,
        events_processed=state.events_processed,
        queue_size=state.queue_size,
        events_total=state.events_processed,
        alerts_total=len(timeline),
        highest_level=highest,
        last_event_time=(
            state.recent_events[-1].timestamp.isoformat() if state.recent_events else None
        ),
        last_alert_time=(timeline[-1].timestamp.isoformat() if timeline else None),
        analyzers_enabled=sum(1 for analyzer in state.analyzers if getattr(analyzer, "enabled", True)),
        snapshot_available=bool(
            state.snapshot_manager and state.snapshot_manager.last_baseline_file
            and state.snapshot_manager.last_baseline_file.exists()
        ),
        report_available=state.report_available(),
    )


def _assessment_to_alert_item(
    assessment: RiskAssessment,
    alert_manager: AlertManager | None = None,
) -> AlertItem:
    """Convert an internal RiskAssessment to an API alert DTO."""
    metadata = alert_manager.get_metadata(assessment) if alert_manager else {}
    signals = [_signal_to_item(signal) for signal in assessment.signals]
    return AlertItem(
        timestamp=assessment.timestamp.isoformat(),
        event_type=assessment.event.event_type,
        src_path=assessment.event.src_path,
        dest_path=assessment.event.dest_path,
        score=assessment.score,
        level=assessment.level,
        analyzers=[signal.analyzer_name for signal in assessment.signals],
        signal_types=[signal.signal_type for signal in assessment.signals],
        signals=signals,
        escalated=bool(metadata.get("escalated", False)),
        escalation_reason=metadata.get("escalation_reason"),
    )


def _signal_to_item(signal: AnalysisSignal) -> SignalItem:
    """Convert an AnalysisSignal to an API DTO."""
    return SignalItem(
        analyzer_name=signal.analyzer_name,
        signal_type=signal.signal_type,
        value=signal.value,
        weight=signal.weight,
        evidence=signal.evidence,
        timestamp=signal.timestamp.isoformat(),
    )


def _event_to_item(event: FileEvent, assessment: RiskAssessment | None = None) -> EventItem:
    """Convert an internal FileEvent to an API event DTO."""
    return EventItem(
        timestamp=event.timestamp.isoformat(),
        event_type=event.event_type,
        src_path=event.src_path,
        dest_path=event.dest_path,
        file_size=event.file_size,
        is_directory=event.is_directory,
        score=assessment.score if assessment else None,
        level=assessment.level if assessment else None,
        signals_count=len(assessment.signals) if assessment else 0,
    )


def _level_counts(timeline: list[RiskAssessment]) -> LevelCounts:
    """Return alert counts by level."""
    counts = Counter(assessment.level.upper() for assessment in timeline)
    return LevelCounts(
        LOW=counts["LOW"],
        MEDIUM=counts["MEDIUM"],
        HIGH=counts["HIGH"],
        CRITICAL=counts["CRITICAL"],
    )


def _highest_level(levels: Iterable[str]) -> str:
    """Return the highest risk level in a sequence."""
    highest = "LOW"
    for level in levels:
        normalized = level.upper()
        if _LEVEL_ORDER.get(normalized, 0) > _LEVEL_ORDER.get(highest, 0):
            highest = normalized
    return highest


def _analyzer_items(state: ApiRuntimeState) -> list[AnalyzerItem]:
    """Build analyzer status rows from configured analyzers and timeline signals."""
    signals_by_analyzer: Counter[str] = Counter()
    last_by_analyzer: dict[str, str] = {}
    for assessment in state.recent_assessments:
        for signal in assessment.signals:
            signals_by_analyzer[signal.analyzer_name] += 1
            last_by_analyzer[signal.analyzer_name] = signal.timestamp.isoformat()

    items: list[AnalyzerItem] = []
    for analyzer in state.analyzers:
        name = getattr(analyzer, "name", analyzer.__class__.__name__)
        items.append(
            AnalyzerItem(
                name=name,
                enabled=bool(getattr(analyzer, "enabled", True)),
                weight=float(getattr(analyzer, "weight", 1.0)),
                signals_total=signals_by_analyzer[name],
                last_triggered_at=last_by_analyzer.get(name),
            )
        )
    return items


def _report_status(
    state: ApiRuntimeState,
    ok: bool = True,
    generated_at: str | None = None,
) -> ReportStatusResponse:
    """Build report status DTO."""
    report_path = Path(state.report_file)
    timeline = _report_timeline(state)
    available = report_path.exists()
    mtime = datetime.fromtimestamp(report_path.stat().st_mtime).isoformat() if available else None
    return ReportStatusResponse(
        ok=ok,
        report_file=str(report_path),
        available=available,
        generated_at=generated_at or mtime,
        events_total=len(timeline),
        alerts_total=sum(1 for assessment in timeline if assessment.signals),
    )


def _report_timeline(state: ApiRuntimeState) -> list[RiskAssessment]:
    """Return report timeline from AlertManager, runtime assessments, or JSONL."""
    if state.alert_manager:
        timeline = state.alert_manager.get_timeline()
        if timeline:
            return timeline
    if state.recent_assessments:
        return list(state.recent_assessments)
    return _load_assessments_from_jsonl(Path(state.log_file))


def _safe_report_path(path: str) -> Path:
    """Resolve report output and reject obviously unsafe locations."""
    resolved = Path(path).resolve()
    cwd = Path.cwd().resolve()
    sandbox = (cwd / "experiments" / "sandbox").resolve()
    for allowed_root in (cwd, sandbox):
        try:
            resolved.relative_to(allowed_root)
        except ValueError:
            continue
        return resolved
    raise ValueError(f"report path is outside the project workspace: {resolved}")


def _load_assessments_from_jsonl(log_file: Path) -> list[RiskAssessment]:
    """Load RiskAssessment records from JSONL."""
    if not log_file.exists():
        return []

    timeline: list[RiskAssessment] = []
    with log_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                event_data = item["event"]
                event = FileEvent(
                    timestamp=datetime.fromisoformat(event_data["timestamp"]),
                    event_type=event_data["event_type"],
                    src_path=event_data["src_path"],
                    dest_path=event_data.get("dest_path"),
                    file_size=event_data.get("file_size"),
                    is_directory=bool(event_data.get("is_directory", False)),
                )
                signals = [
                    AnalysisSignal(
                        analyzer_name=signal_data["analyzer_name"],
                        signal_type=signal_data["signal_type"],
                        value=float(signal_data["value"]),
                        weight=float(signal_data["weight"]),
                        evidence=signal_data.get("evidence", {}),
                        timestamp=datetime.fromisoformat(signal_data["timestamp"]),
                    )
                    for signal_data in item.get("signals", [])
                ]
                timeline.append(
                    RiskAssessment(
                        event=event,
                        signals=signals,
                        score=float(item["score"]),
                        level=item["level"],
                        timestamp=datetime.fromisoformat(item["timestamp"]),
                    )
                )
            except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
                logger.warning("Skipping invalid JSONL assessment: %s", exc)
    return timeline


def _sse(event: str, data: dict[str, Any], event_id: int) -> str:
    """Format one Server-Sent Event."""
    payload = json.dumps(data, ensure_ascii=False)
    return f"id: {event_id}\nevent: {event}\ndata: {payload}\n\n"


app = create_app()
