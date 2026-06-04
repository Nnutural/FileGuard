# FileGuard Acceptance Artifact Index

- JSONL event log: `experiments/sandbox/outputs/acceptance_events.jsonl`
- Alert JSON: `experiments/sandbox/outputs/acceptance_alerts.json`
- HTML report: `experiments/sandbox/outputs/acceptance_report.html`
- API status JSON: `experiments/sandbox/outputs/api_status.json`
- API events JSON: `experiments/sandbox/outputs/api_events.json`
- API alerts JSON: `experiments/sandbox/outputs/api_alerts.json`
- OpenAPI JSON: `experiments/sandbox/outputs/api_openapi.json`
- CLI output log: `experiments/sandbox/outputs/monitor_console.log`
- Screenshot monitor stdout: `experiments/sandbox/outputs/monitor_screenshot_stdout.log`
- Screenshot monitor stderr: `experiments/sandbox/outputs/monitor_screenshot_stderr.log`
- Command log: `experiments/sandbox/outputs/command_log.txt`
- Restore verification: `experiments/sandbox/outputs/restore_verification.json`
- Experiment results JSON: `experiments/sandbox/outputs/experiment_results.json`
- CLI evidence note: `experiments/sandbox/screenshots/cli_dashboard_evidence.txt`
- Web/API evidence note: `experiments/sandbox/screenshots/web_api_evidence.txt`
- Screenshot attempt note: `experiments/sandbox/screenshots/screenshot_attempt_error.txt`
- Experiment summary document: `docs/experiment_log.md`

## Summary

| Experiment | Events | Alert records | Highest level | Signals | Result |
|---|---:|---:|---|---|---|
| Normal file operations | 6 | 1 | HIGH | hash_changed | ok |
| Sensitive path access | 4 | 4 | CRITICAL | freq_spike, policy_hit | ok |
| High entropy file | 2 | 2 | CRITICAL | entropy_anomaly, freq_spike | ok |
| Batch frequency anomaly | 32 | 24 | CRITICAL | freq_spike, hash_changed, similarity_drop | ok |
| Ransom-like modification and restore | 25 | 21 | CRITICAL | entropy_anomaly, freq_spike, hash_changed, honeypot_triggered, similarity_drop | ok |
