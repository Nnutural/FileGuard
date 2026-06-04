# -*- coding: utf-8 -*-
"""文件系统监控器。

基于 watchdog 实时捕获指定目录下的所有文件系统事件，
序列化为 FileEvent 并投递至事件队列。
"""

from __future__ import annotations

import logging
import queue

from fileguard.models import FileEvent

logger = logging.getLogger(__name__)


class FileSystemWatcher:
    """文件系统事件监控器。

    职责：
        继承 watchdog 的 FileSystemEventHandler，监控指定目录的
        created / modified / deleted / moved 四类事件，
        将原始事件转化为 FileEvent 后以非阻塞方式投递至事件队列。

    Attributes:
        watch_dirs: 监控目录列表。
        exclude_patterns: 排除的文件模式列表。
        event_queue: 事件投递队列。
    """

    def __init__(
        self,
        watch_dirs: list[str],
        event_queue: queue.Queue[FileEvent],
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

    def start(self) -> None:
        """启动文件系统监控。"""
        # TODO: 创建 watchdog Observer 和自定义 EventHandler
        # TODO: 对每个 watch_dir 调用 observer.schedule() 启动递归监控
        # TODO: 启动 observer 线程
        pass

    def stop(self) -> None:
        """停止文件系统监控。"""
        # TODO: 调用 observer.stop() 和 observer.join() 优雅关闭
        pass
