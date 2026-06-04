# -*- coding: utf-8 -*-
"""告警管理器。

管理告警的生成、去重、冷却和分发。
同一文件 + 同一信号类型在冷却期内不重复告警。
"""

from __future__ import annotations

import logging
from datetime import datetime

from fileguard.models import RiskAssessment

logger = logging.getLogger(__name__)


class AlertManager:
    """告警管理器。

    职责：
        接收 RiskAssessment，基于冷却期去重后记录至告警时间线。
        提供时间线查询接口供报告生成器使用。

    Attributes:
        cooldown_seconds: 同一 (路径, 信号类型) 组合的冷却时间（秒）。
    """

    def __init__(self, cooldown_seconds: float = 30.0) -> None:
        """初始化告警管理器。

        Args:
            cooldown_seconds: 冷却时间（秒），默认 30 秒。
        """
        self.cooldown_seconds = cooldown_seconds
        self._last_alert: dict[tuple[str, str], datetime] = {}
        self._timeline: list[RiskAssessment] = []

    def process(self, assessment: RiskAssessment) -> bool:
        """处理一条风险评估，决定是否发出告警。

        对评估中的每个信号检查冷却期，若所有信号均处于冷却中
        则抑制该条告警；否则记录到时间线并更新冷却状态。

        Args:
            assessment: 待处理的风险评估。

        Returns:
            True 表示该评估产生了新告警，False 表示被冷却抑制。
        """
        if not assessment.signals:
            return False

        now = assessment.timestamp
        has_new_signal = False

        for signal in assessment.signals:
            key = (assessment.event.src_path, signal.signal_type)
            last_time = self._last_alert.get(key)

            if last_time is None or (now - last_time).total_seconds() >= self.cooldown_seconds:
                self._last_alert[key] = now
                has_new_signal = True

        if has_new_signal:
            self._timeline.append(assessment)
            logger.warning(
                "告警 [%s] %.2f — %s %s",
                assessment.level,
                assessment.score,
                assessment.event.event_type,
                assessment.event.src_path,
            )
            return True

        logger.debug(
            "告警被冷却抑制: %s %s",
            assessment.event.event_type,
            assessment.event.src_path,
        )
        return False

    def get_timeline(self) -> list[RiskAssessment]:
        """返回所有已记录的告警时间线。

        Returns:
            按时间顺序排列的 RiskAssessment 列表。
        """
        return list(self._timeline)
