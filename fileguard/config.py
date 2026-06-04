# -*- coding: utf-8 -*-
"""配置加载与校验模块。

从 YAML 文件读取系统配置，校验必填字段完整性，
并提供分析器级别的配置提取接口。
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    """加载并返回 YAML 配置文件内容。

    Args:
        path: 配置文件路径。

    Returns:
        解析后的配置字典。

    Raises:
        FileNotFoundError: 配置文件不存在时抛出，附带友好提示。
        yaml.YAMLError: YAML 格式错误时抛出。
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"配置文件不存在: {config_path.resolve()}\n"
            f"请复制 config.example.yaml 为 config.yaml 并根据需要修改。"
        )

    logger.info("加载配置文件: %s", config_path.resolve())
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    validate_config(config)
    return config


def get_analyzer_config(config: dict, analyzer_name: str) -> dict:
    """提取指定分析器的配置段。

    Args:
        config: 完整配置字典。
        analyzer_name: 分析器名称，对应 analyzers 下的键名。

    Returns:
        该分析器的配置字典；若不存在则返回空字典。
    """
    return config.get("fileguard", {}).get("analyzers", {}).get(analyzer_name, {})


def validate_config(config: dict) -> None:
    """校验配置必填字段是否完整。

    Args:
        config: 完整配置字典。

    Raises:
        ValueError: 必填字段缺失或不合法时抛出。
    """
    fg = config.get("fileguard")
    if fg is None:
        raise ValueError("配置文件缺少顶级 'fileguard' 键。")

    watch_dirs = fg.get("watch_dirs")
    if not watch_dirs:
        raise ValueError("配置项 'fileguard.watch_dirs' 不能为空，请至少指定一个监控目录。")

    scoring = fg.get("scoring", {})
    levels = scoring.get("levels", {})
    required_levels = {"low", "medium", "high", "critical"}
    missing = required_levels - set(levels.keys())
    if missing:
        raise ValueError(
            f"配置项 'fileguard.scoring.levels' 缺少以下等级定义: {', '.join(sorted(missing))}"
        )

    for level_name, bounds in levels.items():
        if not isinstance(bounds, list) or len(bounds) != 2:
            raise ValueError(
                f"评分等级 '{level_name}' 的区间格式不正确，应为 [下界, 上界]。"
            )

    logger.info("配置校验通过。")
