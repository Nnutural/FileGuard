# .claude/CLAUDE.md

@../AGENTS.md

## Source Of Truth

`AGENTS.md` (imported above) is the authoritative spec for architecture, coding
standards, safety rules, build/test commands, and done criteria. This file only
adds Claude Code specific working instructions. When this file and `AGENTS.md`
appear to conflict, follow `AGENTS.md` and flag the discrepancy.

The parent-directory `系统概要设计文档.md` is the product-level design reference.
It is stored with corrupted (mojibake) encoding and also describes planned scope.
Treat the current source tree under `src/fileguard/` as the implementation source
of truth; do not "fix" the document or implement endpoints it describes unless the
task explicitly asks for it.

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
- API (`/api/status`, `/api/events`, `/api/alerts` only): `api/server.py`,
  `api/schemas.py`
- Experiments + acceptance: `experiments/run_acceptance.py` and
  `experiments/simulate_*.py`

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
