# -*- coding: utf-8 -*-
"""模拟敏感文件高频访问脚本。

在 experiments/sandbox/financial/ 目录下快速读取所有文件，
10 秒内完成 20 次访问，模拟对敏感目录的异常高频访问行为。

用途：验证 FileGuard 的敏感路径策略引擎和频率分析器能否
正确识别对受保护目录的异常访问行为。
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

SANDBOX_DIR = Path(__file__).parent / "sandbox" / "financial"
TOTAL_ACCESSES = 20
TIME_LIMIT = 10.0


def run_simulation() -> None:
    """执行敏感文件高频访问模拟。"""
    if not SANDBOX_DIR.exists():
        logger.error("沙箱目录不存在: %s", SANDBOX_DIR.resolve())
        return

    files = sorted(SANDBOX_DIR.iterdir())
    files = [f for f in files if f.is_file()]
    if not files:
        logger.warning("沙箱目录中没有文件。")
        return

    interval = TIME_LIMIT / TOTAL_ACCESSES

    logger.info("开始敏感文件高频访问模拟...")
    logger.info("目标目录: %s", SANDBOX_DIR.resolve())
    logger.info("计划访问次数: %d，间隔: %.2f 秒", TOTAL_ACCESSES, interval)

    access_count = 0
    file_index = 0

    for _ in range(TOTAL_ACCESSES):
        target = files[file_index % len(files)]
        try:
            content = target.read_text(encoding="utf-8")
            access_count += 1
            logger.info(
                "访问 #%02d: %s (%d 字节)",
                access_count,
                target.name,
                len(content),
            )
        except Exception:
            logger.exception("读取文件失败: %s", target.name)

        file_index += 1
        time.sleep(interval)

    logger.info("敏感文件访问模拟结束。共完成 %d 次访问。", access_count)


if __name__ == "__main__":
    run_simulation()
