# -*- coding: utf-8 -*-
"""FastAPI application and routes for FileGuard."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fileguard.api.schemas import (
    AlertItem,
    AlertsResponse,
    EventItem,
    EventsResponse,
    StatusResponse,
)
from fileguard.models import FileEvent, RiskAssessment
from fileguard.scoring.alert import AlertManager

logger = logging.getLogger(__name__)


@dataclass
class ApiRuntimeState:
    """Runtime state exposed through the API layer."""

    running: bool = False
    watch_dirs: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    events_processed: int = 0
    queue_size: int = 0
    recent_events: list[FileEvent] = field(default_factory=list)
    alert_manager: AlertManager | None = None

    def record_event(self, event: FileEvent, queue_size: int = 0) -> None:
        """Record a processed event for API retrieval."""
        self.events_processed += 1
        self.queue_size = queue_size
        self.recent_events.append(event)
        self.recent_events = self.recent_events[-200:]


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
        state: ApiRuntimeState = app.state.runtime_state
        uptime = (datetime.now() - state.started_at).total_seconds()
        return StatusResponse(
            running=state.running,
            watch_dirs=state.watch_dirs,
            uptime_seconds=uptime,
            events_processed=state.events_processed,
            queue_size=state.queue_size,
        )

    @app.get("/api/alerts", response_model=AlertsResponse)
    async def get_alerts() -> AlertsResponse:
        """Return recorded alerts from AlertManager."""
        state: ApiRuntimeState = app.state.runtime_state
        timeline = state.alert_manager.get_timeline() if state.alert_manager else []
        alerts = [_assessment_to_alert_item(assessment) for assessment in timeline]
        return AlertsResponse(total=len(alerts), alerts=alerts)

    @app.get("/api/events", response_model=EventsResponse)
    async def get_events() -> EventsResponse:
        """Return recent file events recorded by the runtime state."""
        state: ApiRuntimeState = app.state.runtime_state
        events = [_event_to_item(event) for event in reversed(state.recent_events)]
        return EventsResponse(total=len(events), events=events)

    return app


def _assessment_to_alert_item(assessment: RiskAssessment) -> AlertItem:
    """Convert an internal RiskAssessment to an API alert DTO."""
    return AlertItem(
        timestamp=assessment.timestamp.isoformat(),
        event_type=assessment.event.event_type,
        src_path=assessment.event.src_path,
        dest_path=assessment.event.dest_path,
        score=assessment.score,
        level=assessment.level,
        analyzers=[signal.analyzer_name for signal in assessment.signals],
    )


def _event_to_item(event: FileEvent) -> EventItem:
    """Convert an internal FileEvent to an API event DTO."""
    return EventItem(
        timestamp=event.timestamp.isoformat(),
        event_type=event.event_type,
        src_path=event.src_path,
        dest_path=event.dest_path,
        file_size=event.file_size,
        is_directory=event.is_directory,
    )


app = create_app()
