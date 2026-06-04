# -*- coding: utf-8 -*-
"""多维度风险评分引擎。

将多个分析器产出的 AnalysisSignal 按权重聚合为综合评分，
并根据配置的等级区间映射为 LOW / MEDIUM / HIGH / CRITICAL。
"""

from __future__ import annotations

import logging
from datetime import datetime

from fileguard.models import AnalysisSignal, FileEvent, RiskAssessment

logger = logging.getLogger(__name__)


class RiskScorer:
    """加权风险评分器。

    评分公式：
        score = Σ(signal.value × signal.weight) / Σ(signal.weight)

    Attributes:
        levels_config: 等级区间配置，如 {"low": [0, 3], "medium": [3, 5], ...}。
    """

    def __init__(self, levels_config: dict) -> None:
        """初始化评分器。

        Args:
            levels_config: 从配置文件加载的等级区间字典。
        """
        self.levels_config = levels_config

    def calculate(
        self, event: FileEvent, signals: list[AnalysisSignal]
    ) -> RiskAssessment:
        """根据信号列表计算综合风险评分并生成评估结果。

        Args:
            event: 触发评估的原始文件事件。
            signals: 各分析器产出的信号列表。

        Returns:
            包含综合评分和风险等级的 RiskAssessment。
        """
        if not signals:
            return RiskAssessment(
                event=event,
                signals=signals,
                score=0.0,
                level="LOW",
                timestamp=datetime.now(),
            )

        weighted_sum = sum(s.value * s.weight for s in signals)
        weight_total = sum(s.weight for s in signals)
        score = weighted_sum / weight_total if weight_total > 0 else 0.0

        score = max(0.0, min(10.0, score))

        level = self._determine_level(score)

        logger.info(
            "风险评分: %.2f (%s) — 事件: %s %s, 信号数: %d",
            score,
            level,
            event.event_type,
            event.src_path,
            len(signals),
        )

        return RiskAssessment(
            event=event,
            signals=signals,
            score=score,
            level=level,
            timestamp=datetime.now(),
        )

    def _determine_level(self, score: float) -> str:
        """根据配置的区间映射返回风险等级字符串。

        Args:
            score: 综合评分值。

        Returns:
            风险等级: LOW / MEDIUM / HIGH / CRITICAL。
        """
        for level_name in ("critical", "high", "medium", "low"):
            bounds = self.levels_config.get(level_name, [0, 0])
            lower, upper = bounds[0], bounds[1]
            if lower <= score < upper or (level_name == "critical" and score >= lower):
                return level_name.upper()

        return "LOW"
