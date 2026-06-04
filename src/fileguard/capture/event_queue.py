# -*- coding: utf-8 -*-
"""事件队列封装。

对标准库 queue.Queue 做轻量工程化包装：
- 队列容量由配置驱动
- 入队非阻塞，队列满时记录 warning 而非阻塞 watchdog 回调线程
- 出队支持超时，供后续 pipeline 消费
"""

from __future__ import annotations

import logging
import queue

from fileguard.models import FileEvent

logger = logging.getLogger(__name__)


class EventQueue:
    """文件事件队列。

    Attributes:
        maxsize: 队列最大容量。
    """

    def __init__(self, maxsize: int = 10000) -> None:
        """初始化事件队列。

        Args:
            maxsize: 队列最大容量，0 表示无限制。
        """
        self.maxsize = maxsize
        self._queue: queue.Queue[FileEvent] = queue.Queue(maxsize=maxsize)

    def put(self, event: FileEvent) -> bool:
        """以非阻塞方式将事件入队。

        队列满时丢弃事件并记录 warning 日志，不阻塞调用线程。

        Args:
            event: 待入队的文件事件。

        Returns:
            True 表示入队成功，False 表示队列已满、事件被丢弃。
        """
        try:
            self._queue.put_nowait(event)
            return True
        except queue.Full:
            logger.warning(
                "事件队列已满 (maxsize=%d)，丢弃事件: %s %s",
                self.maxsize,
                event.event_type,
                event.src_path,
            )
            return False

    def get(self, timeout: float | None = None) -> FileEvent | None:
        """从队列中取出一个事件。

        Args:
            timeout: 等待超时秒数。None 表示无限等待，0 表示立即返回。

        Returns:
            取到的 FileEvent，超时则返回 None。
        """
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def qsize(self) -> int:
        """返回队列中当前的事件数量（近似值）。"""
        return self._queue.qsize()
