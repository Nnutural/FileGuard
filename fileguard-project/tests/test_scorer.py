# -*- coding: utf-8 -*-
"""RiskScorer 单元测试。"""

import unittest
from datetime import datetime

from fileguard.models import AnalysisSignal, FileEvent
from fileguard.scoring.scorer import RiskScorer


class TestRiskScorer(unittest.TestCase):
    """测试加权风险评分引擎。"""

    def setUp(self) -> None:
        """初始化测试用评分器和通用事件。"""
        self.levels_config = {
            "low": [0, 3.0],
            "medium": [3.0, 5.0],
            "high": [5.0, 7.0],
            "critical": [7.0, 10.0],
        }
        self.scorer = RiskScorer(self.levels_config)
        self.event = FileEvent(
            timestamp=datetime.now(),
            event_type="modified",
            src_path="/test/file.txt",
        )

    def test_no_signals(self) -> None:
        """无信号时评分应为 0，等级为 LOW。"""
        result = self.scorer.calculate(self.event, [])
        self.assertAlmostEqual(result.score, 0.0)
        self.assertEqual(result.level, "LOW")

    def test_single_signal(self) -> None:
        """单信号时评分应等于该信号的 value。"""
        signal = AnalysisSignal(
            analyzer_name="TestAnalyzer",
            signal_type="test_signal",
            value=6.0,
            weight=2.0,
            evidence={"detail": "test"},
        )
        result = self.scorer.calculate(self.event, [signal])
        self.assertAlmostEqual(result.score, 6.0)
        self.assertEqual(result.level, "HIGH")

    def test_multiple_signals_weighted(self) -> None:
        """多信号加权计算验证：score = Σ(v*w) / Σ(w)。"""
        signals = [
            AnalysisSignal(
                analyzer_name="A",
                signal_type="type_a",
                value=9.0,
                weight=2.5,
                evidence={},
            ),
            AnalysisSignal(
                analyzer_name="B",
                signal_type="type_b",
                value=8.5,
                weight=3.0,
                evidence={},
            ),
            AnalysisSignal(
                analyzer_name="C",
                signal_type="type_c",
                value=10.0,
                weight=5.0,
                evidence={},
            ),
        ]
        # score = (9*2.5 + 8.5*3 + 10*5) / (2.5+3+5) = (22.5+25.5+50)/10.5 ≈ 9.333
        result = self.scorer.calculate(self.event, signals)
        expected = (9.0 * 2.5 + 8.5 * 3.0 + 10.0 * 5.0) / (2.5 + 3.0 + 5.0)
        self.assertAlmostEqual(result.score, expected, places=3)
        self.assertEqual(result.level, "CRITICAL")

    def test_low_level_boundary(self) -> None:
        """评分恰好在 LOW 区间内。"""
        signal = AnalysisSignal(
            analyzer_name="X",
            signal_type="x",
            value=2.0,
            weight=1.0,
            evidence={},
        )
        result = self.scorer.calculate(self.event, [signal])
        self.assertEqual(result.level, "LOW")


if __name__ == "__main__":
    unittest.main()
