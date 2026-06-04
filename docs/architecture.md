# FileGuard 系统架构

## 总体架构（四层六模块）

```
┌────────────────────────────────────────────────────────────┐
│              Presentation Layer（展示层）                     │
│  CLI Dashboard (rich)  │  JSON/CSV Log  │  HTML Report     │
│  Web Console (React)   │  FastAPI (/api/*)                  │
├────────────────────────────────────────────────────────────┤
│           Risk Assessment Layer（风险评估层）                  │
│  Multi-Dim Risk Scorer        │  Alert Manager              │
├────────────────────────────────────────────────────────────┤
│            Analysis Pipeline（分析流水线）                     │
│  SensitivePath │ Entropy │ Frequency │ Honeypot             │
│  HashDiff      │ FuzzyHash                                  │
├────────────────────────────────────────────────────────────┤
│            Event Capture Layer（事件捕获层）                   │
│  FileSystemWatcher (watchdog)  │  SnapshotManager           │
└────────────────────────────────────────────────────────────┘
```

## 数据流

```
文件系统事件 → FileSystemWatcher → EventQueue → AnalysisPipeline
  → 6 个分析器各自产出 AnalysisSignal
  → RiskScorer 加权聚合
  → AlertManager 去重/冷却
  → CLI Dashboard / JSON Log / HTML Report / Web API
```

## 线程模型

- Main Thread: CLI 主循环 / 事件消费
- Observer Thread: watchdog 文件事件捕获
- Dashboard Thread: rich Live 面板刷新（可选）
- API Thread: uvicorn 服务线程（可选）
