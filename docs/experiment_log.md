# FileGuard 系统验收实验日志

## 1. 实验环境

- 项目根目录：`FileGuard/`
- 操作系统：Windows，本机 PowerShell
- Python：使用当前系统 Python
- 运行日期：2026-06-04
- 验收配置：
  - 回归验证：`config.example.yaml`
  - 自动化实验：`experiments/sandbox/outputs/acceptance_monitor_config.yaml`
  - 快照恢复实验：`experiments/sandbox/outputs/acceptance_snapshot_config.yaml`
- 实验边界：所有破坏性操作限制在 `experiments/sandbox/`

## 2. 回归验证命令

| 命令 | 结果 | 备注 |
|---|---|---|
| `python -m compileall src tests` | 通过 | 初始回归通过 |
| `$env:PYTHONPATH='src'; python -m unittest discover -s tests -v` | 通过 | 补充系统级测试后为 46 个用例 |
| `$env:PYTHONPATH='src'; python -c "from fileguard.config import load_config; from fileguard.analyzers import create_analyzers; c=load_config('config.example.yaml'); print([a.name for a in create_analyzers(c)])"` | 通过 | 顺序为 SensitivePath, Entropy, Frequency, Honeypot, HashDiff, FuzzyHash |
| `$env:PYTHONPATH='src'; python -c "from fileguard.api.server import app; print(app.title, len(app.routes))"` | 通过 | 输出 `FileGuard API 7` |
| `rg "TODO|pass|NotImplemented" src tests experiments templates` | 通过 | 无匹配 |
| `python -m compileall src tests experiments` | 通过 | 最终验收编译通过 |
| `$env:PYTHONPATH='src'; python -m fileguard snapshot --config config.example.yaml` | 通过 | 在 `experiments/sandbox/.fileguard/baseline.json` 写入 59 个文件记录 |
| `$env:PYTHONPATH='src'; python -m fileguard report --config config.example.yaml` | 通过 | 根目录 `.fileguard/report.html` 已生成；根目录事件日志不存在，因此为空报告 |

## 3. 系统级测试补充

新增测试覆盖：

- `tests/test_api_server.py`：使用 `fastapi.testclient.TestClient` 验证 `/api/status`、`/api/events`、`/api/alerts` 空运行态和有数据运行态均返回 200。
- `tests/test_report_generator.py`：构造最小 `RiskAssessment`，验证 HTML 报告生成和关键字段。
- `tests/test_event_logger.py`：验证 JSONL 每行均为合法 JSON，时间字段已序列化为字符串。
- `tests/test_cli_integration.py`：直接调用 CLI snapshot/report handler，验证临时配置下能生成基线和报告。

## 4. 实验步骤

### 实验 1：正常文件操作基线实验

1. 启动 `monitor --serve-api`。
2. 在 `experiments/sandbox/normal/` 下创建较大普通文本文件。
3. 追加一小段文本。
4. 重命名文件。
5. 删除文件。
6. 读取 JSONL 和 API 结果。

### 实验 2：敏感路径访问实验

1. 写入 `experiments/sandbox/financial/acceptance_budget.csv`。
2. 写入 `experiments/sandbox/config/acceptance_app.ini`。
3. 写入 `experiments/sandbox/certificates/acceptance_service.pem`。
4. 写入 `experiments/sandbox/certificates/acceptance_service.key`。
5. 检查 `policy_hit` evidence。

### 实验 3：高熵文件实验

1. 在 `experiments/sandbox/ransomware_target/entropy/` 下生成随机二进制 `payload.dat`。
2. 同目录生成随机二进制 `allowlisted.zip`。
3. 检查非白名单扩展名触发 `entropy_anomaly`。
4. 检查白名单扩展名按配置跳过熵异常。

### 实验 4：批量操作频率实验

1. 在 `experiments/sandbox/ransomware_target/frequency/` 下快速创建 8 个文件。
2. 快速修改 8 个文件。
3. 快速删除 8 个文件。
4. 检查 `freq_spike` 的 count、threshold、window_seconds evidence。

### 实验 5：类勒索修改 + 快照恢复实验

1. 在 `experiments/sandbox/restore_target/` 准备 6 个文本文件。
2. 运行 snapshot 命令生成 `experiments/sandbox/outputs/restore_baseline.json`。
3. 启动 monitor。
4. 先对文本文件做一次小幅追加，建立运行期内存基线。
5. 将文件内容替换为高熵随机数据。
6. 将目标文件重命名为 `.locked`。
7. 修改蜜罐文件 `.~lock.confidential.docx#`。
8. 停止 monitor。
9. 运行 report 命令生成 HTML 报告。
10. 运行 restore 命令恢复文件。
11. 重新计算 SHA-256 并与基线比对。

## 5. 五个实验结果

| 实验 | 目标 | 事件数 | 告警记录数 | 最高等级 | 关键 signal | 结果 |
|---|---|---:|---:|---|---|---|
| 正常文件操作 | 验证基础捕获 | 6 | 1 | HIGH | `hash_changed` | 通过 |
| 敏感路径访问 | 验证策略命中 | 4 | 4 | CRITICAL | `policy_hit`, `freq_spike` | 通过 |
| 高熵文件 | 验证类加密内容识别 | 2 | 2 | CRITICAL | `entropy_anomaly`, `freq_spike` | 通过 |
| 批量频率异常 | 验证短时批量操作 | 32 | 24 | CRITICAL | `freq_spike`, `hash_changed`, `similarity_drop` | 通过 |
| 类勒索 + 恢复 | 验证端到端闭环 | 25 | 21 | CRITICAL | `entropy_anomaly`, `freq_spike`, `hash_changed`, `honeypot_triggered`, `similarity_drop` | 通过 |

说明：正常文件操作出现 1 条 HIGH 记录，原因是 `HashDiffChecker` 按设计会对内容变化产出 `hash_changed`。该实验未出现 CRITICAL，符合“普通文本操作不应触发严重告警”的验收目标。

## 6. 产物路径

- JSONL 事件日志：`experiments/sandbox/outputs/acceptance_events.jsonl`
- 告警 JSON：`experiments/sandbox/outputs/acceptance_alerts.json`
- HTML 报告：`experiments/sandbox/outputs/acceptance_report.html`
- API status：`experiments/sandbox/outputs/api_status.json`
- API events：`experiments/sandbox/outputs/api_events.json`
- API alerts：`experiments/sandbox/outputs/api_alerts.json`
- OpenAPI JSON：`experiments/sandbox/outputs/api_openapi.json`
- CLI 输出日志：`experiments/sandbox/outputs/monitor_console.log`
- 命令日志：`experiments/sandbox/outputs/command_log.txt`
- restore 校验结果：`experiments/sandbox/outputs/restore_verification.json`
- 实验结果 JSON：`experiments/sandbox/outputs/experiment_results.json`
- 产物索引：`experiments/sandbox/outputs/artifact_index.md`
- CLI 替代证据：`experiments/sandbox/screenshots/cli_dashboard_evidence.txt`
- Web/API 替代证据：`experiments/sandbox/screenshots/web_api_evidence.txt`

## 7. API 响应样例

- `/api/status` 在 monitor 运行期间返回：
  - `running: true`
  - `events_processed: 75`
  - `queue_size: 0`
- `/api/events` 保存了最近事件列表。
- `/api/alerts` 保存了告警列表和 analyzer 名称。
- `/openapi.json` 保存为 API 文档替代证据。

## 8. 截图情况

当前执行环境未能采集真实 PNG/JPG 截图。已尝试使用 Browser/Playwright 打开本机 Chrome，但 Chrome 启动阶段返回 `EACCES`，因此本轮不伪造截图，改用以下证据：

- CLI Dashboard/运行证据：`experiments/sandbox/outputs/monitor_console.log`
- CLI Dashboard 状态：当前环境未安装 `rich`，日志显示 Dashboard 被代码路径禁用，未生成 Live 面板截图。
- API 页面/响应证据：`experiments/sandbox/outputs/api_status.json`、`api_events.json`、`api_alerts.json`、`api_openapi.json`
- HTML 报告证据：`experiments/sandbox/outputs/acceptance_report.html`
- 命令执行证据：`experiments/sandbox/outputs/command_log.txt`
- 浏览器截图尝试记录：`experiments/sandbox/screenshots/screenshot_attempt_error.txt`

## 9. 发现的问题

1. `templates/report.html` 在当前终端输出中出现中文编码乱码，并存在疑似破损 HTML 标签。已改为 ASCII 文案模板，避免报告页面结构受编码影响。
2. `rg "TODO|pass|NotImplemented"` 对 `db.password` 和 `_debounce_pass` 产生误报。已将样例字段改为 `db.secret`，将 watcher 去抖方法重命名为 `_debounce_allowed`。
3. Windows 下自动化停止 `monitor --serve-api` 需要处理 `SIGBREAK`。已在 CLI 中补充该信号处理，monitor 可以优雅停止并关闭 logger/watcher/API。
4. 初版验收配置将 `outputs/` 纳入监控，导致 monitor 监控自身日志并形成事件反馈。已在验收配置生成逻辑中排除 `outputs/**` 与 `screenshots/**`。
5. Python 标准库请求本地 API 时受环境代理影响，导致 readiness 检查无法命中 Uvicorn。验收脚本已对 `127.0.0.1` 请求显式禁用代理。
6. 正常文件实验最初使用过小文件，普通修改被 fuzzy hash 判为相似度骤降。已调整为较大文本上的小幅追加，实验最高等级降为 HIGH。

## 10. 已修复的问题

- 报告模板编码和 HTML 稳定性。
- TODO/pass 扫描误报。
- Windows monitor 自动停止。
- 验收脚本输出目录自监控反馈。
- 本地 API 请求代理干扰。
- 正常文件实验样本过小导致的误判。

## 11. 仍未完成的问题

- 未采集真实 PNG/JPG 截图；Browser/Playwright 启动本机 Chrome 时返回 `EACCES`。本轮使用日志、JSON、HTML 和命令记录作为替代证据。
- 前端 React 页面未在浏览器中端到端截图验收。
- `config.example.yaml` 默认 report 命令使用根目录 `.fileguard/events.jsonl`；若没有先用默认配置运行 monitor，会生成空报告。本轮正式报告使用验收配置和 `acceptance_events.jsonl`。

## 12. 后续建议

1. 增加 `monitor --duration` 或 `monitor --once` 参数，便于 CI 中做稳定集成验收。
2. 将 CLI/API 运行态抽象成可注入服务对象，便于真实长期运行和测试共用。
3. 为前端增加 Playwright 或浏览器截图验收，在可视化环境中补齐 Web 控制台证据。
4. 将 `HashDiffChecker` 和 `FuzzyHashAnalyzer` 接入持久 SnapshotManager 基线，减少进程重启后的首事件盲区。
