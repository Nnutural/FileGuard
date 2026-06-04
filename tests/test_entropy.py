# -*- coding: utf-8 -*-
"""EntropyAnalyzer.calculate_entropy 单元测试。"""

import os
import tempfile
import unittest

from fileguard.analyzers.entropy import EntropyAnalyzer


class TestCalculateEntropy(unittest.TestCase):
    """测试 Shannon 熵计算函数。"""

    def test_all_zero_bytes(self) -> None:
        """全零字节文件的熵值应为 0.0。"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(b"\x00" * 1024)
            path = f.name
        try:
            entropy = EntropyAnalyzer.calculate_entropy(path)
            self.assertAlmostEqual(entropy, 0.0, places=5)
        finally:
            os.unlink(path)

    def test_random_bytes(self) -> None:
        """伪随机字节文件的熵值应接近 8.0。"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(os.urandom(65536))
            path = f.name
        try:
            entropy = EntropyAnalyzer.calculate_entropy(path)
            self.assertGreater(entropy, 7.5)
            self.assertLessEqual(entropy, 8.0)
        finally:
            os.unlink(path)

    def test_plain_text(self) -> None:
        """普通英文文本文件的熵值应在 3.0 ~ 6.0 之间。"""
        content = (
            "The quick brown fox jumps over the lazy dog. "
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
        ) * 50
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".txt", mode="w", encoding="utf-8"
        ) as f:
            f.write(content)
            path = f.name
        try:
            entropy = EntropyAnalyzer.calculate_entropy(path)
            self.assertGreater(entropy, 3.0)
            self.assertLess(entropy, 6.0)
        finally:
            os.unlink(path)

    def test_empty_file(self) -> None:
        """空文件的熵值应为 0.0。"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            path = f.name
        try:
            entropy = EntropyAnalyzer.calculate_entropy(path)
            self.assertAlmostEqual(entropy, 0.0, places=5)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
