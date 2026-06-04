# -*- coding: utf-8 -*-
"""FileGuard — 基于多维行为分析的文件安全风险感知与防护验证系统。"""

import logging

__version__ = "0.1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
