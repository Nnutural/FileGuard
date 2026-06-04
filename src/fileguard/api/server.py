# -*- coding: utf-8 -*-
"""FastAPI 应用与路由定义。

暴露 /api/status、/api/alerts、/api/events 等接口，
供前端通过 HTTP 获取监控数据。
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fileguard.api.schemas import (
    AlertsResponse,
    EventsResponse,
    StatusResponse,
)

logger = logging.getLogger(__name__)


def create_app(cors_origins: list[str] | None = None) -> FastAPI:
    """创建并返回 FastAPI 应用实例。

    Args:
        cors_origins: 允许的 CORS 来源列表。

    Returns:
        配置好路由和中间件的 FastAPI 实例。
    """
    app = FastAPI(
        title="FileGuard API",
        version="0.1.0",
        description="文件安全风险感知与防护验证系统后端接口",
    )

    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/api/status", response_model=StatusResponse)
    async def get_status() -> StatusResponse:
        """获取系统运行状态。"""
        # TODO: 从运行中的 monitor 实例获取真实数据
        return StatusResponse(
            running=False,
            watch_dirs=[],
            uptime_seconds=0.0,
            events_processed=0,
            queue_size=0,
        )

    @app.get("/api/alerts", response_model=AlertsResponse)
    async def get_alerts() -> AlertsResponse:
        """获取告警列表。"""
        # TODO: 从 AlertManager timeline 获取真实数据
        return AlertsResponse(total=0, alerts=[])

    @app.get("/api/events", response_model=EventsResponse)
    async def get_events() -> EventsResponse:
        """获取最近文件事件列表。"""
        # TODO: 从事件缓冲区获取真实数据
        return EventsResponse(total=0, events=[])

    return app
