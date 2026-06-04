# -*- coding: utf-8 -*-
"""HashDiffChecker.compute_sha256 单元测试。"""

import hashlib
import os
import tempfile
import unittest

from fileguard.analyzers.hash_diff import HashDiffChecker


class TestComputeSha256(unittest.TestCase):
    """测试 SHA-256 计算函数。"""

    def test_known_content(self) -> None:
        """已知内容的文件应产出可预测的哈希值。"""
        content = b"Hello, FileGuard!"
        expected = hashlib.sha256(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(content)
            path = f.name
        try:
            result = HashDiffChecker.compute_sha256(path)
            self.assertEqual(result, expected)
        finally:
            os.unlink(path)

    def test_empty_file(self) -> None:
        """空文件的 SHA-256 应等于空字节串的哈希。"""
        expected = hashlib.sha256(b"").hexdigest()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            path = f.name
        try:
            result = HashDiffChecker.compute_sha256(path)
            self.assertEqual(result, expected)
        finally:
            os.unlink(path)

    def test_large_file(self) -> None:
        """大文件（超过单次读取块大小）的哈希计算应正确。"""
        content = os.urandom(256 * 1024)  # 256 KB
        expected = hashlib.sha256(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(content)
            path = f.name
        try:
            result = HashDiffChecker.compute_sha256(path)
            self.assertEqual(result, expected)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
