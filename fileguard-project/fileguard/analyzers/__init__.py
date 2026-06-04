# -*- coding: utf-8 -*-
"""分析器集合包。

提供工厂函数 create_analyzers，根据配置实例化所有已启用的分析器。
"""

from __future__ import annotations

import logging

from fileguard.analyzers.base import BaseAnalyzer
from fileguard.analyzers.entropy import EntropyAnalyzer
from fileguard.analyzers.frequency import FrequencyAnalyzer
from fileguard.analyzers.fuzzy_hash import FuzzyHashAnalyzer
from fileguard.analyzers.hash_diff import HashDiffChecker
from fileguard.analyzers.honeypot import HoneypotSentinel
from fileguard.analyzers.sensitive_path import SensitivePathAnalyzer

logger = logging.getLogger(__name__)

_ANALYZER_REGISTRY: dict[str, type[BaseAnalyzer]] = {
    "sensitive_path": SensitivePathAnalyzer,
    "entropy": EntropyAnalyzer,
    "frequency": FrequencyAnalyzer,
    "honeypot": HoneypotSentinel,
    "hash_diff": HashDiffChecker,
    "fuzzy_hash": FuzzyHashAnalyzer,
}


def create_analyzers(config: dict) -> list[BaseAnalyzer]:
    """根据配置文件实例化所有已启用的分析器。

    Args:
        config: 完整的 fileguard 配置字典（顶级为 'fileguard' 键）。

    Returns:
        已启用的分析器实例列表。
    """
    analyzers_config = config.get("fileguard", {}).get("analyzers", {})
    instances: list[BaseAnalyzer] = []

    for name, analyzer_cls in _ANALYZER_REGISTRY.items():
        analyzer_conf = analyzers_config.get(name, {})
        if not analyzer_conf.get("enabled", True):
            logger.info("分析器 %s 已禁用，跳过。", name)
            continue
        instance = analyzer_cls(analyzer_conf)
        instances.append(instance)
        logger.info("已加载分析器: %s (权重=%.1f)", instance.name, instance.weight)

    return instances
