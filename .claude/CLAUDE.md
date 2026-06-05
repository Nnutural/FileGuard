# .claude/CLAUDE.md

@../AGENTS.md

## Source Of Truth

`AGENTS.md` (imported above) is the authoritative spec for architecture, coding
standards, safety rules, build/test commands, and done criteria. This file only
adds Claude Code specific working instructions. When this file and `AGENTS.md`
appear to conflict, follow `AGENTS.md` and flag the discrepancy.

The parent-directory `系统概要设计文档.md` is the product-level design reference.
Read it explicitly as UTF-8 if PowerShell output appears as mojibake. It also
describes planned scope. Treat the current source tree under `src/fileguard/`
and `frontend/` as the implementation source of truth; do not implement features
from the design document unless the task explicitly asks for them.

## Working Mode

Before editing code, inspect the relevant module and its existing test
(`tests/test_<topic>.py`) so changes match established patterns.

Prefer plan mode for any change that spans multiple files or crosses layers
(capture / analyzers / scoring / output / api / frontend).

Make focused changes that preserve existing public interfaces. Do not perform
broad architectural rewrites, rename CLI arguments, or reorder the analyzer
factory unless the task explicitly requires it.

Do not modify `frontend/` unless the task explicitly concerns the web dashboard
or API integration.

Do not commit, push, or run destructive git commands unless explicitly asked.

## Tooling Preferences

When codegraph is available, use it before editing or answering architecture,
flow, location, or impact questions. Prefer `codegraph_explore` for broad
questions and `codegraph_search` / `codegraph_node` for exact symbol lookups.

Use the dedicated Read / Grep / Glob tools instead of shell `cat` / `grep` /
`find`. This environment is Windows + PowerShell: use PowerShell syntax
(`$env:PYTHONPATH='src'`, `$null`, backtick line continuation), not bash idioms.

All backend commands require `$env:PYTHONPATH='src'` because the package lives
under `src/`. The CLI defaults to `--config config.yaml`; pass
`--config config.example.yaml` when running against the example config.

## Implementation Map

Use this to locate code quickly; see `AGENTS.md` for the responsibility contract.

- Models / data flow: `src/fileguard/models.py`, `src/fileguard/pipeline.py`
- Config loading + validation: `src/fileguard/config.py`
- CLI entry + subcommands (`monitor`, `snapshot`, `restore`, `report`):
  `src/fileguard/cli.py`
- Capture: `capture/watcher.py`, `capture/event_queue.py`, `capture/snapshot.py`
- Analyzers (factory order fixed): `analyzers/__init__.py` registers
  `sensitive_path` → `entropy` → `frequency` → `honeypot` → `hash_diff` →
  `fuzzy_hash`; all extend `analyzers/base.py`
- Scoring: `scoring/scorer.py`, `scoring/alert.py`
- Output: `output/dashboard.py`, `output/logger.py`, `output/report.py`
- API (`/api/status`, `/api/events`, `/api/alerts`, `/api/analyzers`,
  `/api/snapshots`, `/api/reports`, `POST /api/reports`, `/api/stream`):
  `api/server.py`, `api/schemas.py`
- Frontend API and state: `frontend/src/api/fileguard.ts`,
  `frontend/src/hooks/useFileGuardData.ts`, `frontend/src/types.ts`
- Active frontend shell/pages after the Figma Make migration:
  `frontend/src/App.tsx`, `frontend/src/components/fileguard/`,
  `frontend/src/components/ui/`, `frontend/src/styles/`
- Legacy frontend views: `frontend/src/views/*` may still exist but are not the
  active UI unless imported by `App.tsx`
- Experiments + acceptance: `experiments/run_acceptance.py` and
  `experiments/simulate_*.py`

## Roadmap Gap Notes

The final roadmap in `../系统概要设计文档.md` is mostly implemented, but keep these
gaps explicit when reporting status:

- Day 9 is partial: experiment scripts and acceptance workflow exist, but manual
  screenshots/final artifacts must be regenerated for a report.
- Day 10-11 is partial: HTML report generation exists; automated PDF export or a
  finished PDF write-up is not implemented in code.
- `/api/events` and `/api/alerts` do not support pagination, cursors, or
  persistent JSONL query/filter parameters.
- The frontend is presentation-only. It does not edit backend config, start/stop
  monitors, or inspect local files directly.
- OS hardening integrations such as NTFS ACL changes, Windows Controlled Folder
  Access, VSS scheduling, notifications, and Windows service installation are
  not implemented.
- Automatic remediation outside `experiments/sandbox/` is intentionally out of
  scope unless a separate safe design is requested.

## Verification (run after backend-impacting changes)

```powershell
python -m compileall src tests experiments
$env:PYTHONPATH='src'; python -m unittest discover -s tests -v
```

Run the relevant focused test while iterating, e.g.
`$env:PYTHONPATH='src'; python -m unittest tests.test_entropy -v`.

Run the acceptance workflow only when the task touches experiments, reporting,
restore, API integration, or system-level behavior:

```powershell
$env:PYTHONPATH='src'; python experiments/run_acceptance.py
```

For frontend-impacting changes, run `npm run build` from `frontend/`.

If a command cannot run in the current environment, state the reason and provide
the closest safe alternative rather than skipping verification silently.

## Safety Reminders For This Repo

Confirm any destructive or ransomware-like filesystem operation targets a path
under `experiments/sandbox/` before running it. Never operate on real documents,
home directories, system paths, or anything outside the repo.

Log metadata only — never log sensitive file contents.

## Reporting

End each task by reporting: files modified, checks run with their exact results,
and any behavior left unverified. Do not claim a check passed unless it was run.
