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

_REQUIRED_ANALYZERS = frozenset({
    "sensitive_path",
    "entropy",
    "frequency",
    "honeypot",
    "hash_diff",
    "fuzzy_hash",
})

_REQUIRED_LEVELS = frozenset({"low", "medium", "high", "critical"})


def load_config(path: str) -> dict:
    """加载并返回 YAML 配置文件内容。

    Args:
        path: 配置文件路径（绝对或相对于当前工作目录）。

    Returns:
        解析后的完整配置字典。

    Raises:
        FileNotFoundError: 配置文件不存在时抛出，附带友好提示。
        ValueError: YAML 内容为空或结构不符合要求时抛出。
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

    if not isinstance(config, dict):
        raise ValueError(
            f"配置文件内容无效（期望 YAML 映射，实际得到 {type(config).__name__}）。"
        )

    validate_config(config)
    return config


def get_analyzer_config(config: dict, analyzer_name: str) -> dict:
    """提取指定分析器的配置段。

    Args:
        config: 完整配置字典（顶层含 'fileguard' 键）。
        analyzer_name: 分析器名称，对应 analyzers 下的键名。

    Returns:
        该分析器的配置字典；若不存在则返回空字典。
    """
    return (
        config
        .get("fileguard", {})
        .get("analyzers", {})
        .get(analyzer_name, {})
    )


def validate_config(config: dict) -> None:
    """校验配置必填字段是否完整。

    校验项：
        - 顶层 ``fileguard`` 键存在
        - ``watch_dirs`` 非空
        - 6 个分析器配置段齐全
        - ``scoring.levels`` 包含 low/medium/high/critical
        - ``general.debounce_ms`` 和 ``general.max_queue_size`` 可读取
        - ``api.host`` 和 ``api.port`` 可读取

    Args:
        config: 完整配置字典。

    Raises:
        ValueError: 必填字段缺失或不合法时抛出。
    """
    fg = config.get("fileguard")
    if not isinstance(fg, dict):
        raise ValueError("配置文件缺少顶级 'fileguard' 键。")

    # ── watch_dirs ──
    watch_dirs = fg.get("watch_dirs")
    if not watch_dirs:
        raise ValueError(
            "配置项 'fileguard.watch_dirs' 不能为空，请至少指定一个监控目录。"
        )

    # ── analyzers ──
    analyzers = fg.get("analyzers")
    if not isinstance(analyzers, dict):
        raise ValueError("配置项 'fileguard.analyzers' 缺失或不是映射类型。")

    missing_analyzers = _REQUIRED_ANALYZERS - set(analyzers.keys())
    if missing_analyzers:
        raise ValueError(
            f"配置项 'fileguard.analyzers' 缺少以下分析器: "
            f"{', '.join(sorted(missing_analyzers))}"
        )

    # ── scoring.levels ──
    scoring = fg.get("scoring", {})
    levels = scoring.get("levels", {})
    if not isinstance(levels, dict):
        raise ValueError("配置项 'fileguard.scoring.levels' 缺失或不是映射类型。")

    missing_levels = _REQUIRED_LEVELS - set(levels.keys())
    if missing_levels:
        raise ValueError(
            f"配置项 'fileguard.scoring.levels' 缺少以下等级定义: "
            f"{', '.join(sorted(missing_levels))}"
        )

    for level_name, bounds in levels.items():
        if not isinstance(bounds, list) or len(bounds) != 2:
            raise ValueError(
                f"评分等级 '{level_name}' 的区间格式不正确，应为 [下界, 上界]。"
            )

    # ── general ──
    general = fg.get("general", {})
    if not isinstance(general, dict):
        raise ValueError("配置项 'fileguard.general' 缺失或不是映射类型。")

    if "debounce_ms" not in general:
        raise ValueError("配置项 'fileguard.general.debounce_ms' 缺失。")
    if "max_queue_size" not in general:
        raise ValueError("配置项 'fileguard.general.max_queue_size' 缺失。")

    # ── api ──
    api = fg.get("api", {})
    if not isinstance(api, dict):
        raise ValueError("配置项 'fileguard.api' 缺失或不是映射类型。")

    if "host" not in api:
        raise ValueError("配置项 'fileguard.api.host' 缺失。")
    if "port" not in api:
        raise ValueError("配置项 'fileguard.api.port' 缺失。")

    logger.info("配置校验通过。")
