# FileGuard Round 4 Experiment Log

## Scope

Round 4 does not run long stability tests or require screenshots. It focuses on
web-console completeness and system capability completion.

## Demo Command

```powershell
$env:PYTHONPATH='src'; python experiments/run_demo.py --config config.example.yaml
```

The demo writes only under `experiments/sandbox/outputs/`.

## Covered Scenarios

1. Normal file modification.
2. Sensitive path and key-file policy hits.
3. Alert escalation from repeated policy hits.
4. High-entropy ransomware-like content replacement.
5. Hash/fuzzy-hash change observation.
6. Runtime incremental snapshot records.
7. Dry-run defensive auto-restore candidate selection.
8. Report trigger and API sample generation.

## Artifacts

See `experiments/sandbox/outputs/artifact_index.md` after running the demo.

## Verification

Required verification commands:

```powershell
python -m compileall src tests experiments
$env:PYTHONPATH='src'; python -m unittest discover -s tests -v
$env:PYTHONPATH='src'; python experiments/run_demo.py --config config.example.yaml
$env:PYTHONPATH='src'; python -c "from fileguard.api.server import app; print(app.title, len(app.routes))"
cd frontend
npm install
npm run typecheck
npm run build
forbidden placeholder scan across src, tests, experiments, templates, frontend, and docs
```
