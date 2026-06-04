# -*- coding: utf-8 -*-
"""正常文件操作模拟脚本。

在 experiments/sandbox/documents/ 目录下模拟日常文件操作：
  - 每隔 3 秒创建 1 个新文本文件
  - 每隔 5 秒随机编辑 1 个已有文件（追加一行时间戳）
  - 每隔 10 秒删除最早创建的 1 个临时文件

持续运行 3 分钟（180 秒）后自动停止。

用途：验证 FileGuard 在正常操作下不产生误报。
"""

from __future__ import annotations

import logging
import random
import time
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

SANDBOX_DIR = Path(__file__).parent / "sandbox" / "documents"
DURATION_SECONDS = 180
CREATE_INTERVAL = 3
EDIT_INTERVAL = 5
DELETE_INTERVAL = 10


def run_simulation() -> None:
    """执行正常文件操作模拟。"""
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    created_files: list[Path] = []
    file_counter = 100

    start_time = time.monotonic()
    last_create = start_time
    last_edit = start_time
    last_delete = start_time

    logger.info("开始正常操作模拟，持续 %d 秒...", DURATION_SECONDS)
    logger.info("目标目录: %s", SANDBOX_DIR.resolve())

    while (time.monotonic() - start_time) < DURATION_SECONDS:
        now = time.monotonic()

        if now - last_create >= CREATE_INTERVAL:
            file_counter += 1
            new_file = SANDBOX_DIR / f"normal_{file_counter:04d}.txt"
            new_file.write_text(
                f"File created at {datetime.now().isoformat()}\n"
                f"This is a normal test file #{file_counter}.\n",
                encoding="utf-8",
            )
            created_files.append(new_file)
            logger.info("创建文件: %s", new_file.name)
            last_create = now

        if now - last_edit >= EDIT_INTERVAL:
            existing = [f for f in created_files if f.exists()]
            if existing:
                target = random.choice(existing)
                with target.open("a", encoding="utf-8") as f:
                    f.write(f"Edited at {datetime.now().isoformat()}\n")
                logger.info("编辑文件: %s", target.name)
            last_edit = now

        if now - last_delete >= DELETE_INTERVAL:
            if created_files:
                oldest = created_files.pop(0)
                if oldest.exists():
                    oldest.unlink()
                    logger.info("删除文件: %s", oldest.name)
            last_delete = now

        time.sleep(0.5)

    logger.info("正常操作模拟结束。剩余文件数: %d", len([f for f in created_files if f.exists()]))


if __name__ == "__main__":
    run_simulation()
