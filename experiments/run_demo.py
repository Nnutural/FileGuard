# -*- coding: utf-8 -*-
"""Run a safe FileGuard round-4 demo inside experiments/sandbox."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient

from fileguard.analyzers import create_analyzers
from fileguard.api.server import ApiRuntimeState, create_app
from fileguard.capture.snapshot import SnapshotManager
from fileguard.config import load_config
from fileguard.models import FileEvent, RiskAssessment
from fileguard.output.logger import EventLogger
from fileguard.pipeline import AnalysisPipeline
from fileguard.scoring.alert import AlertManager
from fileguard.scoring.scorer import RiskScorer

SANDBOX = ROOT / "experiments" / "sandbox"
OUTPUTS = SANDBOX / "outputs"
DEMO_ROOT = SANDBOX / "demo_round4"
EVENT_LOG = OUTPUTS / "demo_events.jsonl"
ALERTS_JSON = OUTPUTS / "demo_alerts.json"
REPORT_HTML = OUTPUTS / "demo_report.html"
SUMMARY_JSON = OUTPUTS / "demo_summary.json"
ARTIFACT_INDEX = OUTPUTS / "artifact_index.md"


def main() -> None:
    """Run the demo and write all declared artifacts."""
    parser = argparse.ArgumentParser(description="Run a safe FileGuard demo.")
    parser.add_argument("--config", default="config.example.yaml", help="Config path")
    args = parser.parse_args()

    config = load_config(args.config)
    fg = config["fileguard"]
    prepare_demo_tree()
    demo_config = build_demo_config(fg)

    snapshot_manager = SnapshotManager(demo_config["snapshot"])
    snapshot_manager.build_baseline(str(DEMO_ROOT))
    alert_manager = AlertManager(
        cooldown_seconds=0,
        escalation_config={"enabled": True, "window_seconds": 120, "threshold": 2, "group_by": "signal_type"},
    )
    analyzers = create_analyzers({"fileguard": demo_config})
    pipeline = AnalysisPipeline(
        analyzers,
        RiskScorer(demo_config["scoring"]["levels"]),
        alert_manager,
    )

    assessments: list[RiskAssessment] = []
    with EventLogger(str(EVENT_LOG)) as logger:
        for event in build_events():
            assessment = pipeline.process_event(event)
            snapshot_manager.update_incremental(event)
            snapshot_manager.auto_restore_if_needed(
                assessment,
                sandbox_root=str(SANDBOX),
                enabled=True,
                dry_run=True,
            )
            logger.log(assessment)
            assessments.append(assessment)

    REPORT_HTML.parent.mkdir(parents=True, exist_ok=True)
    api_state = ApiRuntimeState(
        running=False,
        watch_dirs=[str(DEMO_ROOT)],
        alert_manager=alert_manager,
        analyzers=analyzers,
        snapshot_manager=snapshot_manager,
        log_file=str(EVENT_LOG),
        report_file=str(REPORT_HTML),
    )
    for assessment in assessments:
        api_state.record_assessment(assessment)
    if snapshot_manager.last_baseline_file is not None:
        snapshot_manager.restore(str(snapshot_manager.last_baseline_file), str(DEMO_ROOT))

    client = TestClient(create_app(runtime_state=api_state))
    client.post("/api/reports")
    save_api_samples(client)

    alerts_payload = client.get("/api/alerts").json()
    ALERTS_JSON.write_text(json.dumps(alerts_payload["alerts"], ensure_ascii=False, indent=2), encoding="utf-8")
    summary = build_summary(client, alert_manager, snapshot_manager)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_artifact_index(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("Next: cd frontend; npm run build")


def prepare_demo_tree() -> None:
    """Prepare only demo-owned files under experiments/sandbox."""
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    if DEMO_ROOT.exists():
        shutil.rmtree(DEMO_ROOT)
    DEMO_ROOT.mkdir(parents=True, exist_ok=True)
    for path in [
        EVENT_LOG,
        ALERTS_JSON,
        REPORT_HTML,
        SUMMARY_JSON,
        OUTPUTS / "demo_api_status.json",
        OUTPUTS / "demo_api_events.json",
        OUTPUTS / "demo_api_alerts.json",
        OUTPUTS / "demo_api_analyzers.json",
        OUTPUTS / "demo_api_snapshots.json",
        OUTPUTS / "demo_api_reports.json",
    ]:
        if path.exists():
            path.unlink()

    (DEMO_ROOT / "normal").mkdir()
    (DEMO_ROOT / "financial").mkdir()
    (DEMO_ROOT / "certificates").mkdir()
    (DEMO_ROOT / "restore_target").mkdir()
    (DEMO_ROOT / "normal" / "readme.txt").write_text("normal baseline\n" * 80, encoding="utf-8")
    (DEMO_ROOT / "financial" / "budget.csv").write_text("quarter,revenue\nQ1,100\n", encoding="utf-8")
    (DEMO_ROOT / "certificates" / "service.key").write_text("PRIVATE KEY DEMO\n", encoding="utf-8")
    for index in range(1, 4):
        (DEMO_ROOT / "restore_target" / f"doc_{index}.txt").write_text(
            f"restore baseline {index}\n" * 120,
            encoding="utf-8",
        )


def build_demo_config(fg: dict[str, Any]) -> dict[str, Any]:
    """Build a narrow demo config using the project scoring and analyzer shapes."""
    demo = dict(fg)
    demo["watch_dirs"] = [str(DEMO_ROOT)]
    demo["snapshot"] = {
        "enabled": True,
        "backup_files": True,
        "backup_dir": str(OUTPUTS / "demo_backups"),
        "baseline_file": str(OUTPUTS / "demo_baseline.json"),
        "incremental_file": str(OUTPUTS / "demo_incremental_snapshots.jsonl"),
        "max_file_size_mb": 5,
    }
    demo["output"] = {
        "log_file": str(EVENT_LOG),
        "report_file": str(REPORT_HTML),
        "dashboard_refresh_ms": 500,
    }
    demo["analyzers"] = dict(fg["analyzers"])
    demo["analyzers"]["frequency"] = {
        **demo["analyzers"]["frequency"],
        "thresholds": {"created": 4, "modified": 4, "deleted": 4, "moved": 4},
    }
    demo["analyzers"]["sensitive_path"] = {
        **demo["analyzers"]["sensitive_path"],
        "policies": [
            {"name": "demo-financial", "pattern": "**/financial/**", "risk_base": 4.5},
            {"name": "demo-key", "pattern": "**/*.key", "risk_base": 4.5},
        ],
    }
    return demo


def build_events() -> list[FileEvent]:
    """Create deterministic file mutations and matching FileEvent objects."""
    events: list[FileEvent] = []

    def event(path: Path, event_type: str = "modified") -> FileEvent:
        return FileEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            src_path=str(path.resolve()),
            file_size=path.stat().st_size if path.exists() else None,
            is_directory=False,
        )

    normal = DEMO_ROOT / "normal" / "readme.txt"
    normal.write_text(normal.read_text(encoding="utf-8") + "small edit\n", encoding="utf-8")
    events.append(event(normal))

    # Two medium policy hits demonstrate escalation to HIGH.
    for path in [DEMO_ROOT / "financial" / "budget.csv", DEMO_ROOT / "certificates" / "service.key"]:
        path.write_text(path.read_text(encoding="utf-8") + "metadata update\n", encoding="utf-8")
        events.append(event(path))

    # Prime hash and fuzzy baselines, then replace with high entropy content.
    target = DEMO_ROOT / "restore_target" / "doc_1.txt"
    events.append(event(target))
    target.write_bytes(os.urandom(32768))
    events.append(event(target))

    # Batch modifications for frequency signals.
    for index in range(2, 4):
        path = DEMO_ROOT / "restore_target" / f"doc_{index}.txt"
        path.write_text(path.read_text(encoding="utf-8") + "burst\n", encoding="utf-8")
        events.append(event(path))

    return events


def save_api_samples(client: TestClient) -> None:
    """Write API sample JSON artifacts."""
    routes = {
        "status": "/api/status",
        "events": "/api/events",
        "alerts": "/api/alerts",
        "analyzers": "/api/analyzers",
        "snapshots": "/api/snapshots",
        "reports": "/api/reports",
    }
    for name, route in routes.items():
        response = client.get(route)
        (OUTPUTS / f"demo_api_{name}.json").write_text(
            json.dumps(response.json(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def build_summary(
    client: TestClient,
    alert_manager: AlertManager,
    snapshot_manager: SnapshotManager,
) -> dict[str, Any]:
    """Build demo summary JSON."""
    events = client.get("/api/events").json()
    alerts = client.get("/api/alerts").json()
    reports = client.get("/api/reports").json()
    signal_counts: Counter[str] = Counter()
    for alert in alerts["alerts"]:
        signal_counts.update(alert.get("signal_types", []))
    return {
        "events_total": events["total"],
        "alerts_total": alerts["total"],
        "highest_level": client.get("/api/status").json()["highest_level"],
        "signals_by_type": dict(signal_counts),
        "alerts_by_level": alerts["by_level"],
        "escalations_total": alert_manager.escalations_total,
        "incremental_snapshots_total": len(snapshot_manager.incremental_records),
        "auto_restore_mode": "dry-run",
        "auto_restore_candidates": len(snapshot_manager.auto_restore_actions),
        "snapshot_verified": snapshot_manager.last_restore_verified,
        "report_file": reports["report_file"],
        "generated_at": reports["generated_at"],
    }


def write_artifact_index(summary: dict[str, Any]) -> None:
    """Write a Markdown artifact index for the demo run."""
    def rel(path: Path) -> str:
        return path.relative_to(ROOT).as_posix()

    lines = [
        "# FileGuard Round 4 Demo Artifacts",
        "",
        f"- Demo events JSONL: `{rel(EVENT_LOG)}`",
        f"- Demo alerts JSON: `{rel(ALERTS_JSON)}`",
        f"- Demo report HTML: `{rel(REPORT_HTML)}`",
        f"- Demo summary JSON: `{rel(SUMMARY_JSON)}`",
        f"- API status sample: `{rel(OUTPUTS / 'demo_api_status.json')}`",
        f"- API events sample: `{rel(OUTPUTS / 'demo_api_events.json')}`",
        f"- API alerts sample: `{rel(OUTPUTS / 'demo_api_alerts.json')}`",
        f"- API analyzers sample: `{rel(OUTPUTS / 'demo_api_analyzers.json')}`",
        f"- API snapshots sample: `{rel(OUTPUTS / 'demo_api_snapshots.json')}`",
        f"- API reports sample: `{rel(OUTPUTS / 'demo_api_reports.json')}`",
        "",
        "## Summary",
        "",
        f"- Events: {summary['events_total']}",
        f"- Alerts: {summary['alerts_total']}",
        f"- Highest level: {summary['highest_level']}",
        f"- Escalations: {summary['escalations_total']}",
        f"- Incremental snapshots: {summary['incremental_snapshots_total']}",
        f"- Auto-restore mode: {summary['auto_restore_mode']}",
    ]
    ARTIFACT_INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
