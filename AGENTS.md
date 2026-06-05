# AGENTS.md

## Purpose

FileGuard is a defensive, Windows-oriented local file security risk sensing and protection validation system.

Use the system overview design document in the parent directory as the product-level reference, and use the current source tree as the implementation source of truth. If the design document describes an endpoint or feature that the code has not implemented yet, treat it as planned scope and say so explicitly.

The system combines:

- Sensitive file access auditing.
- Batch file behavior anomaly detection.
- Ransomware-like encryption behavior sensing.
- Snapshot backup, restore, and integrity verification.
- CLI, FastAPI, HTML report, and React dashboard presentation.

This is a defensive security project. Keep all experiments transparent, bounded, and reversible.

## Repository Layout

```text
src/fileguard/
  api/                 FastAPI app, schemas, and runtime API state
  analyzers/           Sensitive path, entropy, frequency, honeypot, hash diff, fuzzy hash
  capture/             File watcher, event queue, snapshot manager
  output/              CLI dashboard, JSONL event logger, HTML report generator
  scoring/             Risk scorer and alert manager
  cli.py               argparse CLI entrypoint
  config.py            YAML config loading and validation
  models.py            Core dataclasses
  pipeline.py          Analyzer orchestration

frontend/              React + TypeScript + Vite web dashboard
templates/             Jinja2 HTML report template
tests/                 unittest-based tests
experiments/           Safe simulations and acceptance workflow
docs/                  Architecture and experiment notes
config.example.yaml    Example runtime config
pyproject.toml         Python package metadata and dependencies
```

Do not create a nested `FileGuard/FileGuard/` project directory.

## Current Implementation Snapshot

As of the current source tree, verified through codegraph, the project implements:

- Repository structure, YAML config loading, `FileSystemWatcher`, and `EventQueue`.
- Six analyzer classes in the stable factory order listed below.
- `AnalysisPipeline`, `RiskScorer`, and `AlertManager` with timeline, deduplication, cooldown, and escalation metadata.
- `SnapshotManager` baseline creation, content backup, restore with SHA-256 verification, incremental snapshot records, and sandbox-bound optional auto-restore.
- CLI subcommands for `monitor`, `snapshot`, `restore`, and `report`.
- JSONL assessment logging, terminal dashboard output, and Jinja2 HTML report generation.
- FastAPI runtime API with 8 routes, including SSE streaming.
- React + TypeScript + Vite frontend that reads backend API data through `frontend/src/api/fileguard.ts` and `frontend/src/hooks/useFileGuardData.ts`, with demo fallback when the API is unavailable.
- Safe experiment scripts plus the standard acceptance workflow under `experiments/`.
- Unittest coverage across analyzers, scoring, pipeline, snapshots, API, reports, CLI, frontend contract-adjacent behavior, and acceptance helpers.

The Figma Make migrated dashboard lives primarily under `frontend/src/components/fileguard/`, `frontend/src/components/ui/`, and `frontend/src/styles/`. Older `frontend/src/views/*` files may remain in the tree, but if they are not imported by `App.tsx`, treat them as legacy scaffolding rather than the active UI.

## Architecture Contract

Preserve the four-layer design from the overview document:

1. Event Capture Layer: `FileSystemWatcher`, `EventQueue`, `SnapshotManager`.
2. Analysis Pipeline Layer: six independent analyzers.
3. API & Risk Assessment Layer: `RiskScorer`, `AlertManager`, JSONL event store, FastAPI service.
4. Presentation Layer: CLI dashboard, React console, HTML report.

The core data flow is:

```text
FileSystemWatcher
  -> EventQueue
  -> AnalysisPipeline
  -> Analyzer(s)
  -> RiskScorer
  -> AlertManager
  -> JSONL Logger / CLI Dashboard / FastAPI / HTML Report / React Console
```

Keep module responsibilities strict:

- `capture/` captures events and manages snapshots; it must not score risk.
- `analyzers/` emit `AnalysisSignal | None`; they must not create alerts or write presentation output.
- `pipeline.py` orchestrates analyzers, isolates analyzer failures, and passes signals to scoring.
- `scoring/` computes score, level, alert deduplication, cooldown, and timeline state.
- `output/` handles presentation and report/log generation.
- `api/` exposes DTOs and runtime state; it must not duplicate analyzer or scorer logic.
- `frontend/` displays backend data only; it must not read the local filesystem or reimplement detection logic.

## Design Roadmap Status

The final roadmap in `../系统概要设计文档.md` is a planning reference. The current implementation status is:

| Roadmap item | Current status |
| --- | --- |
| Day 1-2: repository structure, config, `FileSystemWatcher`, `EventQueue` | Implemented |
| Day 3-4: six analyzers with unit tests | Implemented |
| Day 5: `RiskScorer`, `AlertManager`, pipeline scheduling | Implemented |
| Day 6: `SnapshotManager` baseline and restore verification | Implemented, with incremental records and sandbox-bound optional auto-restore added |
| Day 7: FastAPI, JSON logger, CLI dashboard | Implemented; API currently exposes 8 routes, not only the design document's minimal set |
| Day 8: React + TypeScript frontend connected to API | Implemented; current UI is the migrated Figma Make dashboard while preserving API/SSE/demo fallback |
| Day 9: experiment scripts, five experiments, manual screenshots | Partially implemented: scripts and `experiments/run_acceptance.py` exist; manual screenshots and final captured artifacts must be regenerated for each report run |
| Day 10-11: HTML report generator and PDF report writing | Partially implemented: HTML report generation exists; automated PDF export or a final written PDF report is not implemented in code |

## Planned Or Unimplemented Scope

Treat these items as planned scope or reporting tasks unless a user explicitly asks to implement them:

- Automated PDF report export is not implemented. The code generates HTML reports only; any PDF write-up is currently a manual deliverable.
- Automated screenshot/GIF capture for the five experiments is not implemented as a guaranteed workflow artifact. Generate fresh screenshots under `experiments/sandbox/screenshots/` when needed.
- `/api/events` and `/api/alerts` currently return runtime-state collections without pagination, cursoring, or persistent query/filter parameters. Report generation can fall back to JSONL assessments, but there is no general JSONL query API.
- Frontend settings that modify backend configuration, start/stop the monitor, or edit watch directories are not implemented. The dashboard is a presentation layer.
- OS-level hardening integrations mentioned as prevention advice, such as NTFS ACL changes, Windows Controlled Folder Access, VSS scheduling, desktop notifications, email alerts, or Windows service installation, are not implemented.
- Automatic remediation outside `experiments/sandbox/` is intentionally not implemented. Keep auto-restore sandbox-bound unless a formal safe design is requested.
- The design document's experiment descriptions are product-level expectations; the current acceptance workflow is the implementation source of truth for what is automated.

## Implemented API Surface

The current backend exposes:

- `GET /api/status`
- `GET /api/events`
- `GET /api/alerts`
- `GET /api/analyzers`
- `GET /api/snapshots`
- `GET /api/reports`
- `POST /api/reports`
- `GET /api/stream`

`/api/stream` is a Server-Sent Events endpoint. Use `?once=true` for short smoke checks that should not keep a streaming connection open.

## Analyzer Rules

Keep the analyzer factory order stable unless a task explicitly requires changing it:

1. `SensitivePathAnalyzer`
2. `EntropyAnalyzer`
3. `FrequencyAnalyzer`
4. `HoneypotSentinel`
5. `HashDiffChecker`
6. `FuzzyHashAnalyzer`

Analyzer evidence must be JSON-serializable.

Risk values must stay in the `0.0` to `10.0` range.

Analyzer exceptions should not crash the monitor loop when the pipeline can continue safely. Log failures with context.

Do not add synthetic error signals for exceptions unless a formal error-signal design is requested.

## Build And Run Commands

Use Python 3.10+.

Backend dependency setup, when dependency installation is requested:

```powershell
python -m pip install -e .
```

Run backend syntax checks:

```powershell
python -m compileall src tests experiments
```

Run backend tests:

```powershell
$env:PYTHONPATH='src'; python -m unittest discover -s tests -v
```

Run CLI help smoke checks:

```powershell
$env:PYTHONPATH='src'; python -m fileguard --help
$env:PYTHONPATH='src'; python -m fileguard monitor --help
$env:PYTHONPATH='src'; python -m fileguard snapshot --help
$env:PYTHONPATH='src'; python -m fileguard restore --help
$env:PYTHONPATH='src'; python -m fileguard report --help
```

Create a baseline snapshot:

```powershell
$env:PYTHONPATH='src'; python -m fileguard snapshot --config config.example.yaml
```

Run the monitor:

```powershell
$env:PYTHONPATH='src'; python -m fileguard monitor --config config.example.yaml --verbose
```

Run the monitor with the API:

```powershell
$env:PYTHONPATH='src'; python -m fileguard monitor --config config.example.yaml --verbose --serve-api
```

Generate an HTML report:

```powershell
$env:PYTHONPATH='src'; python -m fileguard report --config config.example.yaml
```

Verify FastAPI app creation:

```powershell
$env:PYTHONPATH='src'; python -c "from fileguard.api.server import app; print(app.title, len(app.routes))"
```

Run the end-to-end acceptance workflow only when the task touches experiments, reporting, restore, API integration, or system-level behavior:

```powershell
$env:PYTHONPATH='src'; python experiments/run_acceptance.py
```

Frontend dependency setup, when frontend work or dependency installation is requested:

```powershell
cd frontend
npm install
```

Build frontend after frontend changes:

```powershell
cd frontend
npm run build
```

The Vite dev server defaults to `http://localhost:5173`. Backend API defaults to `http://127.0.0.1:8000`.

## Coding Standards

Use `pathlib.Path` for filesystem paths. Keep Windows compatibility.

Use Python type hints for public functions and methods.

Use module-level loggers:

```python
logger = logging.getLogger(__name__)
```

Do not use `print()` in production code; use logging. Simulation and CLI utility output may print concise user-facing results when that is already the local pattern.

Public classes and public methods should have concise docstrings.

Keep dataclass models JSON-serializable. Datetime values exposed outside Python must be ISO strings.

Do not silently swallow exceptions. If an exception is intentionally tolerated, log it with enough context.

Avoid broad rewrites. Prefer focused changes that preserve existing public interfaces.

Do not introduce new frameworks unless explicitly requested.

Do not change CLI argument names unless required for a bug fix. If changed, update tests and documentation.

Keep backend dependencies in `pyproject.toml`. Keep frontend dependencies in `frontend/package.json`.

## Frontend Rules

Only modify `frontend/` when the task explicitly concerns the web dashboard or API integration.

Use React + TypeScript + Vite conventions already present in the project.

Keep shared frontend DTOs in `frontend/src/types.ts` aligned with `src/fileguard/api/schemas.py`.

Keep fetch logic centralized in `frontend/src/api/fileguard.ts`.

Keep UI components under `frontend/src/components/`; avoid putting all UI behavior in `App.tsx`.

Use `VITE_API_BASE_URL` for backend URL configuration when needed.

The frontend must not implement detection algorithms, inspect local files directly, or bypass the backend API.

## Testing Requirements

Every code change should include or update tests unless the change is documentation-only.

Use the existing `unittest` style unless the project is intentionally migrated.

Do not add empty tests.

Do not leave new `TODO`, `pass`, or `NotImplemented` in tests or production code.

Use temporary directories for filesystem tests. Do not depend on developer-specific absolute paths.

Do not run long-lived monitor loops in unit tests. Use mocks, fake queues, short-lived subprocesses, or direct function calls.

For API tests, prefer FastAPI `TestClient` when available. If dependencies cannot be installed, test schema conversion or app creation behavior.

For JSONL logging tests:

- Assert the file exists.
- Assert each line is valid JSON.
- Assert key fields are present.
- Assert timestamps are serialized as strings.

For report tests:

- Generate into a temporary directory.
- Assert the HTML file exists.
- Assert core summary fields appear in the output.

For frontend changes:

- Run `npm run build` from `frontend/`.
- Keep TypeScript types synchronized with backend response models.

## Security And Experiment Safety

All destructive or ransomware-like experiments must stay inside:

```text
experiments/sandbox/
```

Never operate on real user documents, system directories, home directories, or paths outside the repository unless explicitly instructed.

Do not implement real malware behavior.

Do not implement persistence, privilege escalation, credential theft, stealth, evasion, or destructive behavior outside `experiments/sandbox/`.

Class-ransomware simulations may only modify test files under `experiments/sandbox/`.

Never delete files outside the sandbox.

Never disable host security controls.

Never exfiltrate files, tokens, credentials, or environment secrets.

Do not log sensitive file contents. Log metadata only unless a controlled test explicitly requires sample content.

## Snapshot And Restore Rules

Snapshot operations must stay within configured watch or sandbox directories.

Backup paths should be deterministic and safe.

Restore must verify integrity after restoration when possible.

Do not overwrite unrelated files.

If restore cannot safely proceed, fail with a clear error message.

## Experiment Workflow

The standard acceptance workflow is implemented in `experiments/run_acceptance.py`.

It covers:

1. Normal file operation baseline.
2. Sensitive path access.
3. High-entropy file behavior.
4. Batch frequency anomaly.
5. Ransomware-like modification plus snapshot restore.

Experiment artifacts should stay under:

```text
experiments/sandbox/outputs/
experiments/sandbox/screenshots/
```

Each experiment result should record:

- Commands run.
- Event count.
- Alert count.
- Highest risk level.
- Triggered signal types.
- Output artifact paths.
- Whether the result matched expectations.

When experiment behavior changes, update:

```text
docs/experiment_log.md
experiments/sandbox/outputs/artifact_index.md
```

## Git And Change Management

Do not commit changes unless explicitly asked.

Do not rewrite git history.

Do not run destructive git commands such as:

```text
git reset --hard
git clean -fd
```

unless explicitly instructed.

Before finishing, report:

- Modified files.
- Tests or checks run.
- Verification results.
- Known remaining issues or unverified behavior.

## Done Criteria

A task is complete only when:

1. The requested change is implemented.
2. Relevant tests are added or updated, unless documentation-only.
3. `python -m compileall src tests experiments` passes for backend-impacting work.
4. `$env:PYTHONPATH='src'; python -m unittest discover -s tests -v` passes for backend-impacting work.
5. `npm run build` passes for frontend-impacting work.
6. No new `TODO`, `pass`, or `NotImplemented` remains.
7. The final response includes exact checks run and their results.
8. Any unverified behavior is clearly marked as unverified.
