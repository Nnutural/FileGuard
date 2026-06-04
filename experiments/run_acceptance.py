# -*- coding: utf-8 -*-
"""Run FileGuard system acceptance experiments inside experiments/sandbox."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SANDBOX = ROOT / "experiments" / "sandbox"
OUTPUTS = SANDBOX / "outputs"
SCREENSHOTS = SANDBOX / "screenshots"
TMP_DIR = OUTPUTS / "tmp"
MONITOR_CONFIG = OUTPUTS / "acceptance_monitor_config.yaml"
SNAPSHOT_CONFIG = OUTPUTS / "acceptance_snapshot_config.yaml"
EVENT_LOG = OUTPUTS / "acceptance_events.jsonl"
REPORT_HTML = OUTPUTS / "acceptance_report.html"
BASELINE_JSON = OUTPUTS / "restore_baseline.json"
MONITOR_CONSOLE = OUTPUTS / "monitor_console.log"
COMMAND_LOG = OUTPUTS / "command_log.txt"
ALERTS_JSON = OUTPUTS / "acceptance_alerts.json"
RESULTS_JSON = OUTPUTS / "experiment_results.json"
RESTORE_JSON = OUTPUTS / "restore_verification.json"

REQUIRED_DIRS = [
    "documents",
    "financial",
    "config",
    "certificates",
    "normal",
    "ransomware_target",
    "restore_target",
    "screenshots",
    "outputs",
]


def main() -> None:
    """Run all acceptance experiments and write artifacts."""
    started_at = datetime.now()
    prepare_sandbox()
    reset_acceptance_outputs()
    write_configs()
    prepare_restore_target()

    command_records: list[dict[str, Any]] = []
    run_command(
        [
            sys.executable,
            "-m",
            "fileguard",
            "snapshot",
            "--config",
            str(SNAPSHOT_CONFIG),
            "--output",
            str(BASELINE_JSON),
        ],
        "snapshot",
        command_records,
    )

    monitor = start_monitor(command_records)
    try:
        wait_for_api()
        results = []
        results.append(run_normal_experiment())
        results.append(run_sensitive_experiment())
        results.append(run_entropy_experiment())
        results.append(run_frequency_experiment())
        results.append(run_ransom_restore_experiment())

        save_api_response("status", "/api/status")
        save_api_response("events", "/api/events")
        save_api_response("alerts", "/api/alerts")
        save_api_response("openapi", "/openapi.json")
        write_text(
            SCREENSHOTS / "cli_dashboard_evidence.txt",
            "CLI dashboard evidence is captured in outputs/monitor_console.log.\n",
        )
        write_text(
            SCREENSHOTS / "web_api_evidence.txt",
            "API evidence is captured as JSON files in experiments/sandbox/outputs/.\n",
        )
    finally:
        stop_monitor(monitor, command_records)

    run_command(
        [
            sys.executable,
            "-m",
            "fileguard",
            "report",
            "--config",
            str(MONITOR_CONFIG),
            "--log-file",
            str(EVENT_LOG),
            "--output",
            str(REPORT_HTML),
        ],
        "report",
        command_records,
    )
    run_command(
        [
            sys.executable,
            "-m",
            "fileguard",
            "restore",
            "--config",
            str(SNAPSHOT_CONFIG),
            "--from-snapshot",
            str(BASELINE_JSON),
            "--target-dir",
            str(SANDBOX / "restore_target"),
        ],
        "restore",
        command_records,
    )

    records = load_event_records()
    alerts = [record for record in records if record.get("signals")]
    ALERTS_JSON.write_text(json.dumps(alerts, ensure_ascii=False, indent=2), encoding="utf-8")
    restore_summary = verify_restore()
    RESTORE_JSON.write_text(
        json.dumps(restore_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    final_results = summarize_results(results, records, restore_summary, started_at)
    RESULTS_JSON.write_text(
        json.dumps(final_results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    COMMAND_LOG.write_text(
        json.dumps(command_records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_artifact_index(final_results)
    print(json.dumps(final_results["summary"], ensure_ascii=False, indent=2))


def prepare_sandbox() -> None:
    """Create required sandbox directories."""
    for name in REQUIRED_DIRS:
        (SANDBOX / name).mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def reset_acceptance_outputs() -> None:
    """Remove artifacts from the prior acceptance run only."""
    for path in [
        EVENT_LOG,
        REPORT_HTML,
        BASELINE_JSON,
        MONITOR_CONSOLE,
        COMMAND_LOG,
        ALERTS_JSON,
        RESULTS_JSON,
        RESTORE_JSON,
        OUTPUTS / "api_status.json",
        OUTPUTS / "api_events.json",
        OUTPUTS / "api_alerts.json",
        OUTPUTS / "api_openapi.json",
        OUTPUTS / "snapshot_command.log",
        OUTPUTS / "report_command.log",
        OUTPUTS / "restore_command.log",
    ]:
        if path.exists():
            path.unlink()
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def write_configs() -> None:
    """Write monitor and snapshot configs used by acceptance experiments."""
    common = """
  exclude_patterns:
    - "Thumbs.db"
    - "desktop.ini"
    - ".fileguard/**"
    - "outputs/**"
    - "screenshots/**"
  analyzers:
    sensitive_path:
      enabled: true
      weight: 2.0
      policies:
        - name: "financial"
          pattern: "**/financial/**"
          risk_base: 6.0
        - name: "config"
          pattern: "**/config/**"
          risk_base: 5.0
        - name: "certificates"
          pattern: "**/*.pem|**/*.key|**/*.pfx|**/*.cer"
          risk_base: 9.0
    entropy:
      enabled: true
      weight: 3.0
      threshold: 6.5
      high_entropy_extensions: [".zip", ".gz", ".jpg", ".png", ".pdf"]
    frequency:
      enabled: true
      weight: 2.5
      window_seconds: 10
      thresholds:
        created: 5
        deleted: 5
        modified: 5
        moved: 5
    honeypot:
      enabled: true
      weight: 5.0
      deploy_count: 3
      filename_templates:
        - "~$budget_draft.tmp"
        - ".~lock.confidential.docx#"
        - "~$annual_report.tmp"
    hash_diff:
      enabled: true
      weight: 1.5
    fuzzy_hash:
      enabled: true
      weight: 3.0
      block_size: 1024
      similarity_threshold: 0.3
  scoring:
    levels:
      low: [0, 3.0]
      medium: [3.0, 5.0]
      high: [5.0, 7.0]
      critical: [7.0, 10.0]
  snapshot:
    enabled: true
    backup_files: true
    max_file_size_mb: 10
    backup_dir: ".fileguard/backups"
    baseline_file: ".fileguard/baseline.json"
  output:
    log_file: "{event_log}"
    report_file: "{report_html}"
    dashboard_refresh_ms: 500
  api:
    host: "127.0.0.1"
    port: 8000
    cors_origins:
      - "http://localhost:5173"
  general:
    debounce_ms: 50
    max_queue_size: 10000
""".format(
        event_log=EVENT_LOG.as_posix(),
        report_html=REPORT_HTML.as_posix(),
    )
    MONITOR_CONFIG.write_text(
        "fileguard:\n"
        f"  watch_dirs:\n    - \"{SANDBOX.as_posix()}\"\n"
        + common,
        encoding="utf-8",
    )
    SNAPSHOT_CONFIG.write_text(
        "fileguard:\n"
        f"  watch_dirs:\n    - \"{(SANDBOX / 'restore_target').as_posix()}\"\n"
        + common,
        encoding="utf-8",
    )


def prepare_restore_target() -> None:
    """Create deterministic files for snapshot and restore validation."""
    target = SANDBOX / "restore_target"
    target.mkdir(parents=True, exist_ok=True)
    for old_locked in target.glob("*.locked"):
        old_locked.unlink()
    for index in range(1, 7):
        (target / f"doc_{index:02d}.txt").write_text(
            f"FileGuard restore baseline document {index}\n" * 20,
            encoding="utf-8",
        )


def start_monitor(command_records: list[dict[str, Any]]) -> subprocess.Popen[str]:
    """Start monitor with API and return the subprocess."""
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["TMP"] = str(TMP_DIR)
    env["TEMP"] = str(TMP_DIR)
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    handle = MONITOR_CONSOLE.open("w", encoding="utf-8", errors="replace")
    command = [
        sys.executable,
        "-m",
        "fileguard",
        "monitor",
        "--config",
        str(MONITOR_CONFIG),
        "--verbose",
        "--serve-api",
    ]
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=env,
        stdout=handle,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=creationflags,
    )
    process._fileguard_log_handle = handle  # type: ignore[attr-defined]
    command_records.append({"name": "monitor_start", "command": command, "pid": process.pid})
    return process


def stop_monitor(process: subprocess.Popen[str], command_records: list[dict[str, Any]]) -> None:
    """Stop monitor cleanly and record the result."""
    if process.poll() is None:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)
    handle = getattr(process, "_fileguard_log_handle", None)
    if handle is not None:
        handle.close()
    command_records.append({"name": "monitor_stop", "returncode": process.returncode})


def wait_for_api() -> None:
    """Wait until the monitor API is available."""
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            with open_local_url("http://127.0.0.1:8000/api/status", timeout=2) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("API did not become ready on http://127.0.0.1:8000")


def run_normal_experiment() -> dict[str, Any]:
    """Run normal create/modify/move/delete operations."""
    normal = SANDBOX / "normal"
    normal.mkdir(parents=True, exist_ok=True)
    path = normal / "normal_ops.txt"
    renamed = normal / "normal_ops_renamed.txt"
    path.write_text(("normal document body\n" * 800), encoding="utf-8")
    time.sleep(0.3)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("small normal edit\n")
    time.sleep(0.3)
    if renamed.exists():
        renamed.unlink()
    path.rename(renamed)
    time.sleep(0.3)
    renamed.unlink()
    time.sleep(1.0)
    return {"id": "normal", "title": "Normal file operations", "path_markers": ["normal/"]}


def run_sensitive_experiment() -> dict[str, Any]:
    """Run sensitive path and certificate operations."""
    financial = SANDBOX / "financial" / "acceptance_budget.csv"
    cfg = SANDBOX / "config" / "acceptance_app.ini"
    cert = SANDBOX / "certificates" / "acceptance_service.pem"
    key = SANDBOX / "certificates" / "acceptance_service.key"
    financial.write_text("quarter,revenue\nQ1,100\n", encoding="utf-8")
    cfg.write_text("mode=acceptance\n", encoding="utf-8")
    cert.write_text("-----BEGIN CERTIFICATE-----\nTEST\n-----END CERTIFICATE-----\n", encoding="utf-8")
    key.write_text("-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----\n", encoding="utf-8")
    time.sleep(1.0)
    return {
        "id": "sensitive",
        "title": "Sensitive path access",
        "path_markers": ["financial/", "config/", "certificates/"],
    }


def run_entropy_experiment() -> dict[str, Any]:
    """Run high-entropy and allowlisted-extension checks."""
    target = SANDBOX / "ransomware_target" / "entropy"
    target.mkdir(parents=True, exist_ok=True)
    (target / "payload.dat").write_bytes(os.urandom(32768))
    (target / "allowlisted.zip").write_bytes(os.urandom(32768))
    time.sleep(1.0)
    return {"id": "entropy", "title": "High entropy file", "path_markers": ["ransomware_target/entropy/"]}


def run_frequency_experiment() -> dict[str, Any]:
    """Run batch create/modify/delete operations."""
    target = SANDBOX / "ransomware_target" / "frequency"
    target.mkdir(parents=True, exist_ok=True)
    files = [target / f"burst_{index:02d}.txt" for index in range(8)]
    for file_path in files:
        file_path.write_text("burst create\n", encoding="utf-8")
    time.sleep(0.5)
    for file_path in files:
        if file_path.exists():
            file_path.write_text("burst modify\n" * 3, encoding="utf-8")
    time.sleep(0.5)
    for file_path in files:
        if file_path.exists():
            file_path.unlink()
    time.sleep(1.5)
    return {"id": "frequency", "title": "Batch frequency anomaly", "path_markers": ["ransomware_target/frequency/"]}


def run_ransom_restore_experiment() -> dict[str, Any]:
    """Run simulated ransomware modification against restore_target."""
    target = SANDBOX / "restore_target"
    files = sorted(target.glob("doc_*.txt"))
    for file_path in files:
        with file_path.open("a", encoding="utf-8") as handle:
            handle.write("baseline observation\n")
    time.sleep(1.0)
    for file_path in files:
        file_path.write_bytes(os.urandom(32768))
    time.sleep(0.5)
    for file_path in files:
        locked = file_path.with_suffix(file_path.suffix + ".locked")
        if locked.exists():
            locked.unlink()
        if file_path.exists():
            file_path.rename(locked)
    honeypot = SANDBOX / ".~lock.confidential.docx#"
    if honeypot.exists():
        honeypot.write_text("honeypot touched during acceptance\n", encoding="utf-8")
    time.sleep(2.0)
    return {
        "id": "ransom_restore",
        "title": "Ransom-like modification and restore",
        "path_markers": ["restore_target/", ".~lock.confidential.docx#"],
    }


def save_api_response(name: str, route: str) -> None:
    """Save one API response to the outputs directory."""
    with open_local_url(f"http://127.0.0.1:8000{route}", timeout=5) as response:
        data = response.read().decode("utf-8")
    parsed = json.loads(data)
    (OUTPUTS / f"api_{name}.json").write_text(
        json.dumps(parsed, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def open_local_url(url: str, timeout: float) -> Any:
    """Open a local URL without using environment proxy settings."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(url, timeout=timeout)


def run_command(command: list[str], name: str, records: list[dict[str, Any]]) -> None:
    """Run a command with project environment and capture output."""
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["TMP"] = str(TMP_DIR)
    env["TEMP"] = str(TMP_DIR)
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
    )
    log_path = OUTPUTS / f"{name}_command.log"
    log_path.write_text(result.stdout, encoding="utf-8", errors="replace")
    records.append(
        {
            "name": name,
            "command": command,
            "returncode": result.returncode,
            "log": str(log_path),
        }
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {name}")


def load_event_records() -> list[dict[str, Any]]:
    """Load JSONL assessment records."""
    records: list[dict[str, Any]] = []
    if not EVENT_LOG.exists():
        return records
    with EVENT_LOG.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def summarize_results(
    experiments: list[dict[str, Any]],
    records: list[dict[str, Any]],
    restore_summary: dict[str, Any],
    started_at: datetime,
) -> dict[str, Any]:
    """Build experiment metrics from JSONL records."""
    level_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
    summary_rows = []
    for experiment in experiments:
        matched = [
            record
            for record in records
            if record_matches(record, experiment["path_markers"])
        ]
        signals = sorted(
            {
                signal.get("signal_type", "")
                for record in matched
                for signal in record.get("signals", [])
                if signal.get("signal_type")
            }
        )
        highest = "LOW"
        for record in matched:
            level = record.get("level", "LOW")
            if level_order.get(level, 0) > level_order.get(highest, 0):
                highest = level
        summary_rows.append(
            {
                "id": experiment["id"],
                "title": experiment["title"],
                "event_count": len(matched),
                "alert_count": sum(1 for record in matched if record.get("signals")),
                "highest_level": highest,
                "signals": signals,
                "result": classify_experiment(experiment["id"], matched, signals, highest, restore_summary),
            }
        )
    return {
        "run_started_at": started_at.isoformat(),
        "run_finished_at": datetime.now().isoformat(),
        "summary": summary_rows,
        "total_records": len(records),
        "total_alert_records": sum(1 for record in records if record.get("signals")),
        "restore": restore_summary,
    }


def record_matches(record: dict[str, Any], markers: list[str]) -> bool:
    """Return True if a record path belongs to an experiment."""
    event = record.get("event", {})
    paths = [str(event.get("src_path", "")), str(event.get("dest_path", ""))]
    normalized = [path.replace("\\", "/") for path in paths]
    return any(marker in path for marker in markers for path in normalized)


def classify_experiment(
    experiment_id: str,
    matched: list[dict[str, Any]],
    signals: list[str],
    highest: str,
    restore_summary: dict[str, Any],
) -> str:
    """Classify whether an experiment met its acceptance criteria."""
    if experiment_id == "normal":
        return "ok" if matched and highest != "CRITICAL" else "partial"
    if experiment_id == "sensitive":
        return "ok" if "policy_hit" in signals else "failed"
    if experiment_id == "entropy":
        return "ok" if "entropy_anomaly" in signals else "failed"
    if experiment_id == "frequency":
        return "ok" if "freq_spike" in signals else "failed"
    if experiment_id == "ransom_restore":
        expected = {"entropy_anomaly", "hash_changed", "similarity_drop"}
        restore_ok = bool(restore_summary.get("all_verified"))
        return "ok" if expected.issubset(set(signals)) and restore_ok else "partial"
    return "unknown"


def verify_restore() -> dict[str, Any]:
    """Verify restored files against the baseline snapshot hashes."""
    if not BASELINE_JSON.exists():
        return {"all_verified": False, "files": []}
    baseline = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    target_root = SANDBOX / "restore_target"
    original_root = Path(baseline.get("target_dir", target_root)).resolve()
    files = []
    for item in baseline.get("files", []):
        source = Path(item["path"]).resolve()
        try:
            relative = source.relative_to(original_root)
        except ValueError:
            relative = Path(source.name)
        destination = target_root / relative
        current_hash = sha256(destination) if destination.exists() else ""
        files.append(
            {
                "path": str(destination),
                "expected_sha256": item["sha256"],
                "actual_sha256": current_hash,
                "verified": current_hash == item["sha256"],
            }
        )
    return {
        "all_verified": bool(files) and all(item["verified"] for item in files),
        "files": files,
    }


def sha256(path: Path) -> str:
    """Return SHA-256 for a file using the standard library."""
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def write_artifact_index(final_results: dict[str, Any]) -> None:
    """Write a Markdown artifact index for Notion transfer."""
    index = OUTPUTS / "artifact_index.md"
    def rel(path: Path) -> str:
        return path.relative_to(ROOT).as_posix()

    lines = [
        "# FileGuard Acceptance Artifact Index",
        "",
        f"- JSONL event log: `{rel(EVENT_LOG)}`",
        f"- Alert JSON: `{rel(ALERTS_JSON)}`",
        f"- HTML report: `{rel(REPORT_HTML)}`",
        f"- API status JSON: `{rel(OUTPUTS / 'api_status.json')}`",
        f"- API events JSON: `{rel(OUTPUTS / 'api_events.json')}`",
        f"- API alerts JSON: `{rel(OUTPUTS / 'api_alerts.json')}`",
        f"- OpenAPI JSON: `{rel(OUTPUTS / 'api_openapi.json')}`",
        f"- CLI output log: `{rel(MONITOR_CONSOLE)}`",
        f"- Command log: `{rel(COMMAND_LOG)}`",
        f"- Restore verification: `{rel(RESTORE_JSON)}`",
        f"- Experiment results JSON: `{rel(RESULTS_JSON)}`",
        f"- CLI evidence note: `{rel(SCREENSHOTS / 'cli_dashboard_evidence.txt')}`",
        f"- Web/API evidence note: `{rel(SCREENSHOTS / 'web_api_evidence.txt')}`",
        "- Experiment summary document: `docs/experiment_log.md`",
        "",
        "## Summary",
        "",
        "| Experiment | Events | Alert records | Highest level | Signals | Result |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in final_results["summary"]:
        lines.append(
            "| {title} | {event_count} | {alert_count} | {highest_level} | {signals} | {result} |".format(
                title=row["title"],
                event_count=row["event_count"],
                alert_count=row["alert_count"],
                highest_level=row["highest_level"],
                signals=", ".join(row["signals"]) or "-",
                result=row["result"],
            )
        )
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """Write UTF-8 text, creating parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
