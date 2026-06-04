# -*- coding: utf-8 -*-
"""分析器抽象基类。

定义所有分析器必须遵循的统一接口，确保 AnalysisPipeline
能够以一致的方式调用任意分析器。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from fileguard.models import AnalysisSignal, FileEvent


class BaseAnalyzer(ABC):
    """所有分析器的抽象基类。

    子类必须实现 ``analyze`` 方法和 ``name`` 属性。
    基类提供启用检查和信号创建的通用能力。

    Attributes:
        config: 该分析器的配置字典。
        enabled: 是否启用。
        weight: 该分析器产出信号的默认权重。
    """

    def __init__(self, config: dict) -> None:
        """初始化分析器。

        Args:
            config: 从 YAML 配置文件中提取的该分析器配置段。
        """
        self.config = config
        self.enabled: bool = config.get("enabled", True)
        self.weight: float = config.get("weight", 1.0)

    @abstractmethod
    def analyze(self, event: FileEvent) -> AnalysisSignal | None:
        """分析单个文件事件，返回风险信号或 None。

        Args:
            event: 待分析的文件系统事件。

        Returns:
            检测到异常时返回 AnalysisSignal，否则返回 None。
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """分析器名称，用于日志和报告。"""
        ...

    def is_enabled(self) -> bool:
        """返回该分析器是否已启用。"""
        return self.enabled

    def create_signal(
        self, signal_type: str, value: float, evidence: dict
    ) -> AnalysisSignal:
        """创建一个 AnalysisSignal 实例。

        自动填入当前分析器的名称和权重。

        Args:
            signal_type: 信号类型标识。
            value: 归一化风险值 (0.0 ~ 10.0)。
            evidence: 证据详情字典。

        Returns:
            构建好的 AnalysisSignal。
        """
        return AnalysisSignal(
            analyzer_name=self.name,
            signal_type=signal_type,
            value=value,
            weight=self.weight,
            evidence=evidence,
        )
