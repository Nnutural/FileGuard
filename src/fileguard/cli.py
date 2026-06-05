# -*- coding: utf-8 -*-
"""Command-line interface for FileGuard."""

from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _handle_monitor(args: argparse.Namespace) -> None:
    """Start watcher, pipeline, JSON logger, and CLI dashboard."""
    from fileguard.analyzers import create_analyzers
    from fileguard.analyzers.honeypot import HoneypotSentinel
    from fileguard.api.server import ApiRuntimeState
    from fileguard.capture.event_queue import EventQueue
    from fileguard.capture.snapshot import SnapshotManager
    from fileguard.capture.watcher import FileSystemWatcher
    from fileguard.config import load_config
    from fileguard.output.dashboard import Dashboard
    from fileguard.output.logger import EventLogger
    from fileguard.pipeline import AnalysisPipeline
    from fileguard.scoring.alert import AlertManager
    from fileguard.scoring.scorer import RiskScorer

    config = load_config(args.config)
    fg = config["fileguard"]

    general = fg.get("general", {})
    max_queue_size = int(general.get("max_queue_size", 10000))
    debounce_ms = int(general.get("debounce_ms", 200))

    event_queue = EventQueue(maxsize=max_queue_size)
    watcher = FileSystemWatcher(
        watch_dirs=fg["watch_dirs"],
        event_queue=event_queue,
        exclude_patterns=fg.get("exclude_patterns", []),
        debounce_ms=debounce_ms,
    )

    analyzers = create_analyzers(config)
    for analyzer in analyzers:
        if isinstance(analyzer, HoneypotSentinel):
            for watch_dir in fg["watch_dirs"]:
                deployed = analyzer.deploy_honeypots(watch_dir)
                logger.info("Deployed %d honeypots under %s", len(deployed), watch_dir)

    alert_config = fg.get("alerting", {})
    alert_manager = AlertManager(
        cooldown_seconds=float(alert_config.get("cooldown_seconds", 30.0)),
        escalation_config=alert_config.get("escalation", {}),
    )
    scorer = RiskScorer(fg.get("scoring", {}).get("levels", {}))
    pipeline = AnalysisPipeline(analyzers, scorer, alert_manager)
    dashboard = Dashboard(fg.get("output", {}))
    output_config = fg.get("output", {})
    event_logger = EventLogger(output_config.get("log_file", ".fileguard/events.jsonl"))
    snapshot_manager = SnapshotManager(fg.get("snapshot", {}))
    if fg.get("snapshot", {}).get("enabled", True):
        for watch_dir in fg["watch_dirs"]:
            try:
                snapshot_manager.build_baseline(watch_dir)
            except Exception:
                logger.exception("Failed to build monitor startup snapshot for %s", watch_dir)
    api_state = ApiRuntimeState(
        running=True,
        watch_dirs=[str(Path(path).resolve()) for path in fg["watch_dirs"]],
        alert_manager=alert_manager,
        analyzers=analyzers,
        snapshot_manager=snapshot_manager,
        log_file=output_config.get("log_file", ".fileguard/events.jsonl"),
        report_file=output_config.get("report_file", ".fileguard/report.html"),
    )
    api_server: Any | None = None
    api_thread: threading.Thread | None = None

    stop_event = threading.Event()

    def _on_signal(signum: int, frame: object) -> None:
        logger.info("Received termination signal (%s); stopping.", signal.Signals(signum).name)
        stop_event.set()

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _on_signal)

    watcher.start()
    dashboard.start()
    if getattr(args, "serve_api", False):
        from fileguard.api.server import create_app
        import uvicorn

        api_config = fg.get("api", {})
        api_app = create_app(api_config.get("cors_origins", []), api_state)
        uvicorn_config = uvicorn.Config(
            api_app,
            host=api_config.get("host", "127.0.0.1"),
            port=int(api_config.get("port", 8000)),
            log_level="info",
        )
        api_server = uvicorn.Server(uvicorn_config)
        api_thread = threading.Thread(target=api_server.run, daemon=True)
        api_thread.start()
        logger.info(
            "FastAPI server started at http://%s:%s",
            api_config.get("host", "127.0.0.1"),
            int(api_config.get("port", 8000)),
        )
    logger.info("FileGuard monitor started. Press Ctrl+C to stop.")

    try:
        while not stop_event.is_set():
            file_event = event_queue.get(timeout=1.0)
            if file_event is None:
                continue
            assessment = pipeline.process_event(file_event)
            try:
                snapshot_manager.update_incremental(file_event)
            except Exception:
                logger.exception("Incremental snapshot update failed for %s", file_event.src_path)
            auto_restore = fg.get("auto_restore", {})
            try:
                snapshot_manager.auto_restore_if_needed(
                    assessment,
                    sandbox_root=str((Path.cwd() / "experiments" / "sandbox").resolve()),
                    enabled=bool(auto_restore.get("enabled", False)),
                    dry_run=bool(auto_restore.get("dry_run", True)),
                )
            except Exception:
                logger.exception("Auto-restore evaluation failed for %s", file_event.src_path)
            event_logger.log(assessment)
            dashboard.update(assessment)
            api_state.record_assessment(assessment, event_queue.qsize())
    finally:
        api_state.running = False
        if api_server is not None:
            api_server.should_exit = True
        if api_thread is not None:
            api_thread.join(timeout=5)
        dashboard.stop()
        event_logger.close()
        watcher.stop()
        timeline = alert_manager.get_timeline()
        highest = "LOW"
        for item in timeline:
            if {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}.get(item.level, 0) > {
                "LOW": 0,
                "MEDIUM": 1,
                "HIGH": 2,
                "CRITICAL": 3,
            }.get(highest, 0):
                highest = item.level
        logger.info(
            "FileGuard summary: events=%d alerts=%d highest=%s escalations=%d incremental_snapshots=%d",
            api_state.events_processed,
            len(timeline),
            highest,
            alert_manager.escalations_total,
            len(snapshot_manager.incremental_records),
        )
        logger.info("FileGuard monitor exited.")


def _handle_snapshot(args: argparse.Namespace) -> None:
    """Build a baseline snapshot for configured watch directories."""
    from fileguard.capture.snapshot import SnapshotManager
    from fileguard.config import load_config

    config = load_config(args.config)
    fg = config["fileguard"]
    snapshot_config = dict(fg.get("snapshot", {}))
    if args.output:
        snapshot_config["baseline_file"] = str(Path(args.output).resolve())

    manager = SnapshotManager(snapshot_config)
    total_files = 0
    for watch_dir in fg.get("watch_dirs", []):
        baseline = manager.build_baseline(watch_dir)
        total_files += len(baseline)
    logger.info("Snapshot baseline complete: %d files", total_files)


def _handle_restore(args: argparse.Namespace) -> None:
    """Restore files from a snapshot and verify hashes."""
    from fileguard.capture.snapshot import SnapshotManager
    from fileguard.config import load_config

    config = load_config(args.config)
    fg = config["fileguard"]
    target_dir = args.target_dir or fg.get("watch_dirs", ["."])[0]
    manager = SnapshotManager(fg.get("snapshot", {}))
    results = manager.restore(args.from_snapshot, target_dir)

    success_count = sum(1 for ok in results.values() if ok)
    logger.info("Restore verified: %d/%d files", success_count, len(results))
    for path, ok in results.items():
        logger.info("%s %s", "PASS" if ok else "FAIL", path)


def _handle_report(args: argparse.Namespace) -> None:
    """Generate an HTML report from a JSONL event log."""
    from fileguard.config import load_config
    from fileguard.output.report import ReportGenerator

    config = load_config(args.config)
    output_config = config["fileguard"].get("output", {})
    log_file = Path(args.log_file or output_config.get("log_file", ".fileguard/events.jsonl"))
    output_path = Path(args.output or output_config.get("report_file", ".fileguard/report.html"))
    template_path = Path("templates") / "report.html"

    timeline = _load_assessments_from_jsonl(log_file)
    generator = ReportGenerator(str(template_path), str(output_path))
    generator.generate(timeline)
    logger.info("Report generated from %d assessments: %s", len(timeline), output_path)


def _handle_demo(args: argparse.Namespace) -> None:
    """Run the safe round-4 demo script."""
    from experiments.run_demo import main as run_demo_main

    original_argv = sys.argv[:]
    try:
        sys.argv = ["run_demo.py", "--config", args.config]
        run_demo_main()
    finally:
        sys.argv = original_argv


def _load_assessments_from_jsonl(log_file: Path) -> list["RiskAssessment"]:
    """Load RiskAssessment records from a JSONL log file."""
    from fileguard.models import AnalysisSignal, FileEvent, RiskAssessment

    if not log_file.exists():
        logger.warning("Log file does not exist: %s", log_file)
        return []

    timeline: list[RiskAssessment] = []
    with log_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                event_data = item["event"]
                event = FileEvent(
                    timestamp=datetime.fromisoformat(event_data["timestamp"]),
                    event_type=event_data["event_type"],
                    src_path=event_data["src_path"],
                    dest_path=event_data.get("dest_path"),
                    file_size=event_data.get("file_size"),
                    is_directory=bool(event_data.get("is_directory", False)),
                )
                signals = [
                    AnalysisSignal(
                        analyzer_name=signal_data["analyzer_name"],
                        signal_type=signal_data["signal_type"],
                        value=float(signal_data["value"]),
                        weight=float(signal_data["weight"]),
                        evidence=signal_data.get("evidence", {}),
                        timestamp=datetime.fromisoformat(signal_data["timestamp"]),
                    )
                    for signal_data in item.get("signals", [])
                ]
                timeline.append(
                    RiskAssessment(
                        event=event,
                        signals=signals,
                        score=float(item["score"]),
                        level=item["level"],
                        timestamp=datetime.fromisoformat(item["timestamp"]),
                    )
                )
            except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
                logger.warning("Skipping invalid JSONL assessment: %s", exc)
    return timeline


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="fileguard",
        description="FileGuard file security risk sensing and protection verification system.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    monitor_parser = subparsers.add_parser("monitor", help="Start real-time monitoring")
    monitor_parser.add_argument("--config", "-c", default="config.yaml", help="Config path")
    monitor_parser.add_argument("--verbose", "-v", action="store_true", help="Enable DEBUG logs")
    monitor_parser.add_argument(
        "--serve-api",
        action="store_true",
        help="Serve FastAPI endpoints while monitoring",
    )
    monitor_parser.set_defaults(handler=_handle_monitor)

    snapshot_parser = subparsers.add_parser("snapshot", help="Build baseline snapshot")
    snapshot_parser.add_argument("--config", "-c", default="config.yaml", help="Config path")
    snapshot_parser.add_argument("--output", "-o", default=None, help="Snapshot output path")
    snapshot_parser.set_defaults(handler=_handle_snapshot)

    restore_parser = subparsers.add_parser("restore", help="Restore files from snapshot")
    restore_parser.add_argument("--config", "-c", default="config.yaml", help="Config path")
    restore_parser.add_argument("--from-snapshot", required=True, help="Snapshot JSON path")
    restore_parser.add_argument("--target-dir", default=None, help="Restore target directory")
    restore_parser.set_defaults(handler=_handle_restore)

    report_parser = subparsers.add_parser("report", help="Generate HTML report from JSONL log")
    report_parser.add_argument("--config", "-c", default="config.yaml", help="Config path")
    report_parser.add_argument("--log-file", default=None, help="JSONL event log path")
    report_parser.add_argument("--output", "-o", default=None, help="Report output path")
    report_parser.set_defaults(handler=_handle_report)

    demo_parser = subparsers.add_parser("demo", help="Run safe round-4 demo artifacts")
    demo_parser.add_argument("--config", "-c", default="config.example.yaml", help="Config path")
    demo_parser.set_defaults(handler=_handle_demo)

    return parser


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if getattr(args, "verbose", False):
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("DEBUG logging enabled.")

    args.handler(args)
