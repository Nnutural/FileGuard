# -*- coding: utf-8 -*-
"""API 响应模型 / DTO。

定义后端接口返回给前端的数据结构，
与内部 dataclass (models.py) 解耦。
"""

from __future__ import annotations

from pydantic import BaseModel


class StatusResponse(BaseModel):
    """系统运行状态响应。"""

    running: bool
    watch_dirs: list[str]
    uptime_seconds: float
    events_processed: int
    queue_size: int


class AlertItem(BaseModel):
    """单条告警条目。"""

    timestamp: str
    event_type: str
    src_path: str
    dest_path: str | None = None
    score: float
    level: str
    analyzers: list[str]


class AlertsResponse(BaseModel):
    """告警列表响应。"""

    total: int
    alerts: list[AlertItem]


class EventItem(BaseModel):
    """单条文件事件条目。"""

    timestamp: str
    event_type: str
    src_path: str
    dest_path: str | None = None
    file_size: int | None = None
    is_directory: bool = False


class EventsResponse(BaseModel):
    """最近事件列表响应。"""

    total: int
    events: list[EventItem]
