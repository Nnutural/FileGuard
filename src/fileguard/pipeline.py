# -*- coding: utf-8 -*-
"""分析流水线主调度模块。

采用责任链模式依次调用各分析器处理文件事件，
收集所有信号后交给评分引擎和告警管理器。
"""

from __future__ import annotations

import logging

from fileguard.analyzers.base import BaseAnalyzer
from fileguard.models import AnalysisSignal, FileEvent, RiskAssessment
from fileguard.scoring.alert import AlertManager
from fileguard.scoring.scorer import RiskScorer

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """分析流水线。

    将 FileEvent 依次送入所有已注册的分析器，收集产出的
    AnalysisSignal，交由 RiskScorer 计算综合评分，
    再由 AlertManager 决定是否发出告警。

    Attributes:
        analyzers: 已注册的分析器列表。
        scorer: 风险评分引擎。
        alert_manager: 告警管理器。
    """

    def __init__(
        self,
        analyzers: list[BaseAnalyzer],
        scorer: RiskScorer,
        alert_manager: AlertManager,
    ) -> None:
        """初始化分析流水线。

        Args:
            analyzers: 已启用的分析器实例列表。
            scorer: 风险评分引擎。
            alert_manager: 告警管理器。
        """
        self.analyzers = analyzers
        self.scorer = scorer
        self.alert_manager = alert_manager

    def process_event(self, event: FileEvent) -> RiskAssessment:
        """处理单个文件系统事件。

        依次调用所有已启用的分析器，收集非 None 的信号，
        计算综合评分，交给告警管理器处理后返回评估结果。

        Args:
            event: 待处理的文件系统事件。

        Returns:
            该事件的综合风险评估结果。
        """
        signals: list[AnalysisSignal] = []

        for analyzer in self.analyzers:
            if not analyzer.is_enabled():
                continue
            try:
                signal = analyzer.analyze(event)
                if signal is not None:
                    signals.append(signal)
                    logger.debug(
                        "分析器 %s 产出信号: type=%s value=%.2f",
                        analyzer.name,
                        signal.signal_type,
                        signal.value,
                    )
            except Exception:
                logger.exception("分析器 %s 处理事件时发生异常", analyzer.name)

        assessment = self.scorer.calculate(event, signals)

        self.alert_manager.process(assessment)

        return assessment
