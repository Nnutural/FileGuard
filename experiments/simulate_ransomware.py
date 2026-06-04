# -*- coding: utf-8 -*-
"""模拟勒索软件行为脚本。

在 experiments/sandbox/documents/ 目录下对所有 .txt 文件执行：
  1. 读取原始内容
  2. 用 base64 编码替换文件内容（模拟加密，不使用真实加密库）
  3. 重命名文件为 原名.locked

每个文件操作间隔 100ms，模拟勒索软件的批量加密行为。

用途：验证 FileGuard 对类勒索软件行为的检测能力。

警告：此脚本仅用于安全研究和测试环境，仅操作 sandbox 目录内的文件。
"""

from __future__ import annotations

import base64
import logging
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

SANDBOX_DIR = Path(__file__).parent / "sandbox" / "documents"
OPERATION_DELAY = 0.1


def run_simulation() -> None:
    """执行模拟勒索软件加密操作。"""
    if not SANDBOX_DIR.exists():
        logger.error("沙箱目录不存在: %s", SANDBOX_DIR.resolve())
        return

    txt_files = sorted(SANDBOX_DIR.glob("*.txt"))
    if not txt_files:
        logger.warning("沙箱目录中没有 .txt 文件。")
        return

    logger.info("开始模拟勒索软件行为...")
    logger.info("目标目录: %s", SANDBOX_DIR.resolve())
    logger.info("目标文件数: %d", len(txt_files))

    encrypted_count = 0

    for file_path in txt_files:
        try:
            original_content = file_path.read_bytes()

            encoded_content = base64.b64encode(original_content)
            file_path.write_bytes(encoded_content)
            logger.info("已加密: %s (原始 %d B → 编码 %d B)",
                        file_path.name, len(original_content), len(encoded_content))

            locked_path = file_path.with_suffix(file_path.suffix + ".locked")
            file_path.rename(locked_path)
            logger.info("已重命名: %s → %s", file_path.name, locked_path.name)

            encrypted_count += 1
            time.sleep(OPERATION_DELAY)

        except Exception:
            logger.exception("处理文件失败: %s", file_path.name)

    logger.info("模拟勒索软件行为结束。共加密 %d 个文件。", encrypted_count)


if __name__ == "__main__":
    run_simulation()
