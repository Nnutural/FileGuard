# FileGuard Round 4 Final Delivery

## Summary

Round 4 completes the web-console-first delivery and fills the system response
loop: real-time API push, report trigger, alert escalation, runtime incremental
snapshots, sandbox-only defensive auto-restore, one-command demo, tests, and
delivery documentation.

## Implemented Features

- Multi-view React console with Overview, Events, Alerts, Analyzers, Snapshots,
  Reports, and Demo/About views.
- Central API client, SSE subscription, polling fallback, explicit demo mode.
- Expanded FastAPI contract with status/events/alerts/analyzers/snapshots/reports/stream.
- `POST /api/reports` HTML report generation.
- `AlertManager` MEDIUM-to-HIGH escalation.
- `SnapshotManager` runtime incremental snapshot records.
- Optional dry-run-first sandbox auto-restore.
- `experiments/run_demo.py` and `python -m fileguard demo`.

## Safety

All destructive and recovery demonstrations are constrained to
`experiments/sandbox/`. Auto-restore is disabled by default, dry-run by default,
and refuses paths outside the sandbox boundary.

## Current Limits

- There is no authentication or persistent database by design.
- SSE is an in-process runtime stream; it is not a message broker.
- Frontend charts are lightweight CSS/SVG rather than a charting dependency.
- Demo data is explicitly marked and never presented as real monitoring data.

## Recommended Demo Flow

1. Run backend tests.
2. Run `python experiments/run_demo.py --config config.example.yaml`.
3. Start backend monitor with `--serve-api`.
4. Start Vite frontend and inspect the dashboard.
5. Trigger report generation from the Reports page.
6. Open `experiments/sandbox/outputs/demo_report.html`.
