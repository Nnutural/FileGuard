# -*- coding: utf-8 -*-
"""JSON Lines 事件日志模块。

将 RiskAssessment 序列化为 JSON 后以 JSONL 格式追加写入日志文件。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from types import TracebackType

from fileguard.models import RiskAssessment

logger = logging.getLogger(__name__)


class EventLogger:
    """JSONL 事件日志记录器。

    支持上下文管理器协议，确保文件句柄正确关闭。

    Attributes:
        log_file: 日志文件路径。
    """

    def __init__(self, log_file: str) -> None:
        """初始化事件日志记录器并打开文件。

        自动创建父目录（若不存在）。

        Args:
            log_file: JSONL 日志文件路径。
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.log_file.open("a", encoding="utf-8")
        logger.info("事件日志已打开: %s", self.log_file.resolve())

    def log(self, assessment: RiskAssessment) -> None:
        """将风险评估序列化为 JSON 并写入一行。

        Args:
            assessment: 待记录的风险评估结果。
        """
        line = json.dumps(assessment.to_dict(), ensure_ascii=False)
        self._handle.write(line + "\n")
        self._handle.flush()

    def close(self) -> None:
        """关闭日志文件句柄。"""
        if self._handle and not self._handle.closed:
            self._handle.close()
            logger.info("事件日志已关闭: %s", self.log_file)

    def __enter__(self) -> EventLogger:
        """进入上下文管理器。"""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """退出上下文管理器时关闭文件。"""
        self.close()
