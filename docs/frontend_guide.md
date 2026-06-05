# FileGuard Frontend Guide

## Structure

- `frontend/src/App.tsx`: shell, top bar, navigation, refresh controls.
- `frontend/src/api/fileguard.ts`: all REST calls and SSE subscription.
- `frontend/src/hooks/useFileGuardData.ts`: data loading, SSE, polling fallback, demo fallback.
- `frontend/src/types.ts`: DTOs aligned with `src/fileguard/api/schemas.py`.
- `frontend/src/demoData.ts`: explicit demo-mode data.
- `frontend/src/components/common.tsx`: badges, cards, tables helpers, drawer, charts.
- `frontend/src/views/`: Overview, Events, Alerts, Analyzers, Snapshots, Reports, Demo.
- `frontend/src/styles.css`: design variables and responsive layout.

## Views

- Overview: monitor status, totals, risk distribution, score trend, event distribution, recent alert.
- Events: searchable, filterable, sortable event table with detail drawer.
- Alerts: level/path filters, score/time sorting, signal detail drawer, escalation metadata.
- Analyzers: six analyzer cards and trigger bar chart.
- Snapshots: baseline, backup, restore verification, incremental snapshot records, auto-restore actions.
- Reports: report status and `POST /api/reports` trigger button.
- Demo/About: data-source mode, connection state, version, demo explanation.

## Real-Time Behavior

The console first tries `GET /api/stream` through `EventSource`. If SSE fails,
it falls back to timed polling. If REST calls fail, it uses `demoData` and shows
a clear Demo data mode banner.

## Build

```powershell
cd frontend
npm install
npm run typecheck
npm run build
```

No new frontend runtime dependencies were added in Round 4; charts and routing
are implemented with React state, CSS, and SVG.
