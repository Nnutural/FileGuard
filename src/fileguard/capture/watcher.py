# -*- coding: utf-8 -*-
"""文件系统监控器。

基于 watchdog 实时捕获指定目录下的所有文件系统事件，
转换为 FileEvent 后以非阻塞方式投递至 EventQueue。
支持多目录递归监听、排除模式过滤和 modified 事件去抖。
"""

from __future__ import annotations

import fnmatch
import logging
import time
from datetime import datetime
from pathlib import Path

from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    DirMovedEvent,
)
from watchdog.observers import Observer

from fileguard.capture.event_queue import EventQueue
from fileguard.models import FileEvent

logger = logging.getLogger(__name__)

_EVENT_TYPE_MAP: dict[type, str] = {
    FileCreatedEvent: "created",
    DirCreatedEvent: "created",
    FileModifiedEvent: "modified",
    DirModifiedEvent: "modified",
    FileDeletedEvent: "deleted",
    DirDeletedEvent: "deleted",
    FileMovedEvent: "moved",
    DirMovedEvent: "moved",
}


class _GuardEventHandler(FileSystemEventHandler):
    """watchdog 事件处理器内部实现。

    将 watchdog 原始事件转换为 FileEvent 并投递至队列，
    同时负责排除模式匹配和 modified 事件去抖。
    """

    def __init__(
        self,
        event_queue: EventQueue,
        exclude_patterns: list[str],
        debounce_ms: int,
    ) -> None:
        super().__init__()
        self._queue = event_queue
        self._exclude_patterns = exclude_patterns
        self._debounce_ms = debounce_ms
        self._last_modified: dict[str, float] = {}

    # ── watchdog 回调 ──

    def on_created(self, event: FileSystemEvent) -> None:
        """处理 created 事件。"""
        self._dispatch(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        """处理 modified 事件，附加去抖逻辑。"""
        self._dispatch(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """处理 deleted 事件。"""
        self._dispatch(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        """处理 moved 事件。"""
        self._dispatch(event)

    # ── 内部方法 ──

    def _dispatch(self, event: FileSystemEvent) -> None:
        """统一事件分发入口。"""
        src_path = str(Path(event.src_path))

        if self._should_exclude(src_path):
            return

        event_type = _EVENT_TYPE_MAP.get(type(event))
        if event_type is None:
            return

        if event_type == "modified" and not self._debounce_pass(src_path):
            return

        dest_path: str | None = None
        if hasattr(event, "dest_path") and event.dest_path:
            dest_path = str(Path(event.dest_path))

        is_directory = event.is_directory

        file_size = self._get_file_size(src_path, is_directory)

        file_event = FileEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            src_path=src_path,
            dest_path=dest_path,
            file_size=file_size,
            is_directory=is_directory,
        )

        self._queue.put(file_event)

    def _should_exclude(self, path: str) -> bool:
        """检查路径是否匹配任一排除模式。"""
        normalized = path.replace("\\", "/")
        name = Path(path).name
        for pattern in self._exclude_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
            if fnmatch.fnmatch(normalized, pattern):
                return True
            if "**" in pattern or "/" in pattern:
                if fnmatch.fnmatch(normalized, f"*/{pattern}"):
                    return True
        return False

    def _debounce_pass(self, path: str) -> bool:
        """对 modified 事件进行去抖，返回 True 表示允许通过。"""
        now = time.monotonic() * 1000
        last = self._last_modified.get(path, 0.0)
        if (now - last) < self._debounce_ms:
            logger.debug("去抖丢弃 modified 事件: %s", path)
            return False
        self._last_modified[path] = now
        return True

    @staticmethod
    def _get_file_size(path: str, is_directory: bool) -> int | None:
        """安全获取文件大小，文件不存在或为目录时返回 None。"""
        if is_directory:
            return None
        try:
            return Path(path).stat().st_size
        except OSError:
            return None


class FileSystemWatcher:
    """文件系统事件监控器。

    使用 watchdog Observer 递归监控多个目录，将文件系统事件
    转换为 FileEvent 后投递至 EventQueue。

    Attributes:
        watch_dirs: 监控目录列表。
        event_queue: 事件投递队列。
        exclude_patterns: 排除的文件模式列表。
        debounce_ms: modified 事件去抖间隔（毫秒）。
    """

    def __init__(
        self,
        watch_dirs: list[str],
        event_queue: EventQueue,
        exclude_patterns: list[str] | None = None,
        debounce_ms: int = 200,
    ) -> None:
        """初始化监控器。

        Args:
            watch_dirs: 待监控的目录路径列表。
            event_queue: FileEvent 投递目标队列。
            exclude_patterns: 需排除的文件 glob 模式。
            debounce_ms: 同一文件 modified 事件的去抖间隔（毫秒）。
        """
        self.watch_dirs = watch_dirs
        self.event_queue = event_queue
        self.exclude_patterns = exclude_patterns or []
        self.debounce_ms = debounce_ms
        self._observer: Observer | None = None

    def start(self) -> None:
        """启动文件系统监控。

        对每个配置的监控目录创建递归监听，启动 Observer 守护线程。
        目录不存在时记录 warning 并跳过。
        """
        handler = _GuardEventHandler(
            event_queue=self.event_queue,
            exclude_patterns=self.exclude_patterns,
            debounce_ms=self.debounce_ms,
        )

        self._observer = Observer()

        for dir_path in self.watch_dirs:
            resolved = Path(dir_path).resolve()
            if not resolved.is_dir():
                logger.warning("监控目录不存在，已跳过: %s", resolved)
                continue
            self._observer.schedule(handler, str(resolved), recursive=True)
            logger.info("已注册监控目录: %s", resolved)

        self._observer.daemon = True
        self._observer.start()
        logger.info("FileSystemWatcher 已启动。")

    def stop(self) -> None:
        """停止文件系统监控并等待 Observer 线程退出。"""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            logger.info("FileSystemWatcher 已停止。")
            self._observer = None
