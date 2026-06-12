# -*- coding: utf-8 -*-
"""模拟敏感文件高频访问脚本。

在 experiments/sandbox/financial/ 目录下快速读取所有文件，
10 秒内完成 20 次访问，模拟对敏感目录的异常高频访问行为。

注意：watchdog 无法稳定捕获普通 open/read 只读访问。为了让 FileGuard
在当前 watchdog 方案下观察到本实验，脚本默认会在每次读取后 touch
同一个文件，只更新文件 mtime，不改写文件内容。

用途：验证 FileGuard 的敏感路径策略引擎和频率分析器能否
正确识别对受保护目录的异常访问行为。
"""

from __future__ import annotations

import argparse
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


def _touch_for_watchdog(target: Path) -> None:
    """Touch the accessed file so watchdog can emit a modified event.

    This updates file metadata only. The file content remains unchanged, so
    hash-based analyzers should not report content changes for this action.
    """
    target.touch(exist_ok=True)


def run_simulation(
    total_accesses: int = TOTAL_ACCESSES,
    time_limit: float = TIME_LIMIT,
    emit_watchdog_events: bool = True,
) -> None:
    """执行敏感文件高频访问模拟。"""
    if not SANDBOX_DIR.exists():
        logger.error("沙箱目录不存在: %s", SANDBOX_DIR.resolve())
        return

    files = sorted(SANDBOX_DIR.iterdir())
    files = [f for f in files if f.is_file()]
    if not files:
        logger.warning("沙箱目录中没有文件。")
        return

    interval = time_limit / total_accesses

    logger.info("开始敏感文件高频访问模拟...")
    logger.info("目标目录: %s", SANDBOX_DIR.resolve())
    logger.info("计划访问次数: %d，间隔: %.2f 秒", total_accesses, interval)
    if emit_watchdog_events:
        logger.info("watchdog 可观测模式: 已启用 touch 元数据事件")
    else:
        logger.info("watchdog 可观测模式: 已关闭，普通只读访问通常不会进入 FileGuard")

    access_count = 0
    file_index = 0

    for _ in range(total_accesses):
        target = files[file_index % len(files)]
        try:
            content = target.read_text(encoding="utf-8")
            if emit_watchdog_events:
                _touch_for_watchdog(target)
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


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the sensitive access simulation."""
    parser = argparse.ArgumentParser(
        description="模拟对 financial 敏感目录的高频访问。"
    )
    parser.add_argument(
        "--accesses",
        type=int,
        default=TOTAL_ACCESSES,
        help="访问次数，默认 20。",
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        default=TIME_LIMIT,
        help="总持续时间秒数，默认 10。",
    )
    parser.add_argument(
        "--no-watchdog-events",
        action="store_true",
        help="只读访问，不 touch 文件；通常不会被 FileGuard 当前 watcher 捕获。",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    run_simulation(
        total_accesses=args.accesses,
        time_limit=args.time_limit,
        emit_watchdog_events=not args.no_watchdog_events,
    )
