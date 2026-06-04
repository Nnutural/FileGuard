# -*- coding: utf-8 -*-
"""核心数据模型定义。

包含 FileEvent、AnalysisSignal、RiskAssessment、FileSnapshot 四个数据类，
作为系统各层之间传递数据的标准结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FileEvent:
    """文件系统原始事件。

    由 FileSystemWatcher 捕获并序列化，作为分析流水线的输入。

    Attributes:
        timestamp: 事件发生时间。
        event_type: 事件类型 (created / modified / deleted / moved)。
        src_path: 源文件路径。
        dest_path: 目标路径，仅 moved 事件有值。
        file_size: 文件大小（字节），可能为 None。
        is_directory: 是否为目录事件。
    """

    timestamp: datetime
    event_type: str
    src_path: str
    dest_path: str | None = None
    file_size: int | None = None
    is_directory: bool = False

    def to_dict(self) -> dict:
        """序列化为可 JSON 化的字典。"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "src_path": self.src_path,
            "dest_path": self.dest_path,
            "file_size": self.file_size,
            "is_directory": self.is_directory,
        }


@dataclass
class AnalysisSignal:
    """单个分析器产出的风险信号。

    每个分析器在检测到异常时生成一个 AnalysisSignal，
    携带归一化风险值、权重和证据详情。

    Attributes:
        analyzer_name: 产生该信号的分析器名称。
        signal_type: 信号类型 (policy_hit / entropy_anomaly / freq_spike 等)。
        value: 归一化风险值 (0.0 ~ 10.0)。
        weight: 该信号在评分中的权重。
        evidence: 证据详情字典。
        timestamp: 信号生成时间。
    """

    analyzer_name: str
    signal_type: str
    value: float
    weight: float
    evidence: dict
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """序列化为可 JSON 化的字典。"""
        return {
            "analyzer_name": self.analyzer_name,
            "signal_type": self.signal_type,
            "value": self.value,
            "weight": self.weight,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class RiskAssessment:
    """对单个事件或事件组的综合风险评估。

    由 RiskScorer 根据多个 AnalysisSignal 加权聚合后生成。

    Attributes:
        event: 触发评估的原始文件事件。
        signals: 所有分析器产出的信号列表。
        score: 加权聚合后的综合评分。
        level: 风险等级 (LOW / MEDIUM / HIGH / CRITICAL)。
        timestamp: 评估生成时间。
    """

    event: FileEvent
    signals: list[AnalysisSignal]
    score: float
    level: str
    timestamp: datetime

    def to_dict(self) -> dict:
        """序列化为可 JSON 化的字典。"""
        return {
            "event": self.event.to_dict(),
            "signals": [s.to_dict() for s in self.signals],
            "score": self.score,
            "level": self.level,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class FileSnapshot:
    """单个文件的快照记录。

    用于建立基线、增量对比和恢复验证。

    Attributes:
        path: 文件路径。
        sha256: 文件内容的 SHA-256 哈希值。
        size: 文件大小（字节）。
        entropy: 文件内容的 Shannon 熵值。
        snapshot_time: 快照建立时间。
        content_backup_path: 备份副本的存储路径，可选。
    """

    path: str
    sha256: str
    size: int
    entropy: float
    snapshot_time: datetime
    content_backup_path: str | None = None

    def to_dict(self) -> dict:
        """序列化为可 JSON 化的字典。"""
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size": self.size,
            "entropy": self.entropy,
            "snapshot_time": self.snapshot_time.isoformat(),
            "content_backup_path": self.content_backup_path,
        }
