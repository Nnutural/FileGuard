# -*- coding: utf-8 -*-
"""熵值分析器。

计算文件 Shannon 熵值，对比基线熵值，检测加密行为。
加密后的文件熵值接近 8.0，正常文本文件通常在 3.5 ~ 5.5 之间。
"""

from __future__ import annotations

import logging
import math
from collections import Counter

from fileguard.analyzers.base import BaseAnalyzer
from fileguard.models import AnalysisSignal, FileEvent

logger = logging.getLogger(__name__)


class EntropyAnalyzer(BaseAnalyzer):
    """Shannon 熵值分析器。

    职责：
        对新创建或被修改的文件计算 Shannon 熵，识别文件内容
        是否被加密（加密后熵值接近 8.0 上限）。

    输入：
        FileEvent — created 或 modified 类型的文件系统事件。

    输出：
        AnalysisSignal(signal_type="entropy_anomaly") 或 None。

    关键算法：
        按字节统计频率分布，应用 Shannon 公式 H = -Σ p(x)·log₂p(x)。
        将计算结果与配置阈值（默认 6.5）对比，同时参考基线快照
        中记录的原始熵值，避免对天然高熵文件（.zip、.jpg 等）误报。
    """

    @property
    def name(self) -> str:
        """分析器名称。"""
        return "EntropyAnalyzer"

    @staticmethod
    def calculate_entropy(file_path: str, block_size: int = 8192) -> float:
        """计算文件内容的 Shannon 熵。

        按字节统计频率分布并应用信息熵公式，结果范围 0.0 ~ 8.0。
        空文件返回 0.0。

        Args:
            file_path: 待计算文件的路径。
            block_size: 每次读取的块大小（字节）。

        Returns:
            文件内容的 Shannon 熵值。
        """
        byte_counts: Counter = Counter()
        total_bytes = 0

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(block_size)
                if not chunk:
                    break
                byte_counts.update(chunk)
                total_bytes += len(chunk)

        if total_bytes == 0:
            return 0.0

        entropy = 0.0
        for count in byte_counts.values():
            p = count / total_bytes
            if p > 0:
                entropy -= p * math.log2(p)

        return entropy

    def analyze(self, event: FileEvent) -> AnalysisSignal | None:
        """分析文件熵值是否出现异常跳变。

        Args:
            event: 待分析的文件系统事件。

        Returns:
            熵值异常时返回 AnalysisSignal，否则返回 None。
        """
        # TODO: 仅处理 created / modified 事件，忽略 deleted / moved
        # TODO: 跳过目录事件
        # TODO: 调用 calculate_entropy 计算当前文件熵值
        # TODO: 检查文件扩展名是否在 high_entropy_extensions 白名单中（跳过天然高熵文件）
        # TODO: 将当前熵值与配置阈值 (threshold) 对比
        # TODO: 若超过阈值，计算归一化风险值并调用 self.create_signal 返回
        return None
