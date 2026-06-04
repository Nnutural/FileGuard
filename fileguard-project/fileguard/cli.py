# -*- coding: utf-8 -*-
"""命令行接口模块。

使用 argparse 实现 FileGuard 的四个子命令：
monitor、snapshot、restore、report。
"""

from __future__ import annotations

import argparse
import logging
import sys

logger = logging.getLogger(__name__)


def _handle_monitor(args: argparse.Namespace) -> None:
    """处理 monitor 子命令。"""
    print(f"[TODO] monitor command not yet implemented (config={args.config})")


def _handle_snapshot(args: argparse.Namespace) -> None:
    """处理 snapshot 子命令。"""
    print(f"[TODO] snapshot command not yet implemented (config={args.config}, output={args.output})")


def _handle_restore(args: argparse.Namespace) -> None:
    """处理 restore 子命令。"""
    print(
        f"[TODO] restore command not yet implemented "
        f"(config={args.config}, from_snapshot={args.from_snapshot}, "
        f"target_dir={args.target_dir})"
    )


def _handle_report(args: argparse.Namespace) -> None:
    """处理 report 子命令。"""
    print(
        f"[TODO] report command not yet implemented "
        f"(config={args.config}, log_file={args.log_file}, output={args.output})"
    )


def build_parser() -> argparse.ArgumentParser:
    """构建并返回命令行参数解析器。

    Returns:
        配置完成的 ArgumentParser 实例。
    """
    parser = argparse.ArgumentParser(
        prog="fileguard",
        description="FileGuard — 基于多维行为分析的文件安全风险感知与防护验证系统",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用子命令")

    # ── monitor ──
    monitor_parser = subparsers.add_parser("monitor", help="启动实时监控")
    monitor_parser.add_argument(
        "--config", "-c", default="config.yaml", help="配置文件路径 (默认: config.yaml)"
    )
    monitor_parser.add_argument(
        "--verbose", "-v", action="store_true", help="启用 DEBUG 日志级别"
    )
    monitor_parser.set_defaults(handler=_handle_monitor)

    # ── snapshot ──
    snapshot_parser = subparsers.add_parser("snapshot", help="建立基线快照")
    snapshot_parser.add_argument(
        "--config", "-c", default="config.yaml", help="配置文件路径 (默认: config.yaml)"
    )
    snapshot_parser.add_argument(
        "--output", "-o", default=None, help="快照输出路径"
    )
    snapshot_parser.set_defaults(handler=_handle_snapshot)

    # ── restore ──
    restore_parser = subparsers.add_parser("restore", help="从快照恢复文件")
    restore_parser.add_argument(
        "--config", "-c", default="config.yaml", help="配置文件路径 (默认: config.yaml)"
    )
    restore_parser.add_argument(
        "--from-snapshot", required=True, help="基线快照文件路径"
    )
    restore_parser.add_argument(
        "--target-dir", default=None, help="恢复目标目录"
    )
    restore_parser.set_defaults(handler=_handle_restore)

    # ── report ──
    report_parser = subparsers.add_parser("report", help="从日志生成 HTML 报告")
    report_parser.add_argument(
        "--config", "-c", default="config.yaml", help="配置文件路径 (默认: config.yaml)"
    )
    report_parser.add_argument(
        "--log-file", default=None, help="事件日志文件路径"
    )
    report_parser.add_argument(
        "--output", "-o", default=None, help="报告输出路径"
    )
    report_parser.set_defaults(handler=_handle_report)

    return parser


def main() -> None:
    """CLI 入口点。"""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if getattr(args, "verbose", False):
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("已启用 DEBUG 日志级别。")

    args.handler(args)
