# FileGuard Demo Guide

## Environment

- Python 3.10+
- Node.js 18+ for the frontend
- PowerShell on Windows is the primary local environment

Backend commands should set:

```powershell
$env:PYTHONPATH='src'
```

## One-Command Demo

```powershell
$env:PYTHONPATH='src'; python experiments/run_demo.py --config config.example.yaml
```

Equivalent CLI wrapper:

```powershell
$env:PYTHONPATH='src'; python -m fileguard demo --config config.example.yaml
```

The demo only writes under `experiments/sandbox/`. It generates normal,
sensitive-path, high-entropy, batch, escalation, incremental snapshot, dry-run
auto-restore, API sample, and HTML report artifacts.

## Demo Artifacts

- `experiments/sandbox/outputs/demo_events.jsonl`
- `experiments/sandbox/outputs/demo_alerts.json`
- `experiments/sandbox/outputs/demo_report.html`
- `experiments/sandbox/outputs/demo_api_status.json`
- `experiments/sandbox/outputs/demo_api_events.json`
- `experiments/sandbox/outputs/demo_api_alerts.json`
- `experiments/sandbox/outputs/demo_api_analyzers.json`
- `experiments/sandbox/outputs/demo_api_snapshots.json`
- `experiments/sandbox/outputs/demo_api_reports.json`
- `experiments/sandbox/outputs/demo_summary.json`
- `experiments/sandbox/outputs/artifact_index.md`

## Backend Manual Demo

```powershell
$env:PYTHONPATH='src'; python -m fileguard snapshot --config config.example.yaml
$env:PYTHONPATH='src'; python -m fileguard monitor --config config.example.yaml --verbose --serve-api
$env:PYTHONPATH='src'; python -m fileguard report --config config.example.yaml
```

API checks:

```powershell
$env:PYTHONPATH='src'; python -c "from fileguard.api.server import app; print(app.title, len(app.routes))"
```

SSE check:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/stream?once=true
```

Report trigger check:

```powershell
Invoke-WebRequest -Method POST http://127.0.0.1:8000/api/reports
```

## Frontend

```powershell
cd frontend
npm install
npm run typecheck
npm run build
npm run dev
```

Set `VITE_API_BASE_URL=http://127.0.0.1:8000` when the Vite dev server should
talk to a backend on a different origin. If the API is unavailable, the console
falls back to explicit Demo data mode and shows a banner.
