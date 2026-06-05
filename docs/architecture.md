# FileGuard Architecture

## Layers

FileGuard keeps the four-layer design from the system overview:

1. Event Capture: `FileSystemWatcher`, `EventQueue`, `SnapshotManager`.
2. Analysis Pipeline: six analyzers emit metadata-only `AnalysisSignal` objects.
3. Risk/API Layer: `RiskScorer`, `AlertManager`, JSONL store, FastAPI service.
4. Presentation: CLI dashboard, React web console, HTML report.

## Runtime Flow

```text
FileSystemWatcher
  -> EventQueue
  -> AnalysisPipeline
  -> SensitivePath / Entropy / Frequency / Honeypot / HashDiff / FuzzyHash
  -> RiskScorer
  -> AlertManager
  -> JSONL Logger
  -> CLI Dashboard / FastAPI / SSE / HTML Report / React Console
```

The core detection algorithms are still isolated in `src/fileguard/analyzers/`
and `src/fileguard/scoring/scorer.py`. Round 4 adds orchestration and delivery
capabilities without rewriting those algorithms.

## API Contract

Current FastAPI routes:

- `GET /api/status`: runtime status, totals, highest level, snapshot/report flags.
- `GET /api/events`: recent event rows, including optional score/level/signal count.
- `GET /api/alerts`: alert timeline, full signal details, escalation metadata, by-level counts.
- `GET /api/analyzers`: analyzer enabled state, weight, trigger totals, last trigger time.
- `GET /api/snapshots`: baseline, backup, restore, incremental snapshot, auto-restore state.
- `GET /api/reports`: report file status.
- `POST /api/reports`: generate an HTML report from current timeline or JSONL.
- `GET /api/stream`: Server-Sent Events stream for status/event/alert updates.

## Round 4 Extensions

Alert escalation:

- Implemented in `AlertManager` with backward-compatible constructor options.
- If enabled, repeated alerts in a time window can escalate from `MEDIUM` to `HIGH`.
- Escalation metadata is exposed through API alert items.

Incremental snapshots:

- Implemented in `SnapshotManager.update_incremental()`.
- Records path, old/new SHA-256, old/new entropy, event type, and timestamp.
- Records are metadata-only and written to a JSONL file under FileGuard metadata paths.

Defensive auto-restore:

- Implemented in `SnapshotManager.auto_restore_if_needed()`.
- Default config is disabled and dry-run.
- Only targets files under `experiments/sandbox/`.
- Uses only FileGuard's own snapshot backup copies.

Report trigger:

- `POST /api/reports` uses `ReportGenerator`.
- Output path is validated to stay under the project workspace.

Frontend:

- `frontend/src/App.tsx` provides a multi-view console with internal tab navigation.
- `frontend/src/hooks/useFileGuardData.ts` centralizes API fetch, SSE subscription,
  polling fallback, and demo-data fallback.
- `frontend/src/demoData.ts` mirrors backend DTO shapes for offline presentation.
