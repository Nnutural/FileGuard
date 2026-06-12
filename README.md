# FileGuard

基于多维行为分析的文件安全风险感知与防护验证系统。

## 功能特性

- **六大分析器**：敏感路径策略、Shannon 熵值分析、滑动窗口频率分析、蜜罐哨兵、SHA-256 哈希比对、模糊哈希相似度分析
- **加权评分引擎**：多维信号归一化加权聚合，四级风险判定（LOW / MEDIUM / HIGH / CRITICAL）
- **快照备份与恢复**：文件基线快照建立、增量更新、一键恢复与完整性校验
- **CLI 实时面板**：基于 rich 的终端仪表盘，实时展示事件流与风险状态
- **HTML 安全报告**：Jinja2 模板驱动，内嵌图表的结构化分析报告
- **配置驱动**：所有阈值与规则通过 YAML 配置管理，零硬编码

## 快速开始

```bash
# 1. 安装依赖
pip install -e .

# 2. 复制并修改配置文件
cp config.example.yaml config.yaml

# 3. 启动实时监控
fileguard monitor --config config.example.yaml --verbose --serve-api
fileguard monitor -c config.yaml
```

## 项目结构

```
fileguard-project/
├── README.md
├── pyproject.toml
├── config.example.yaml
│
├── fileguard/                   # 主包
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                   # 命令行接口
│   ├── config.py                # 配置加载与校验
│   ├── models.py                # 核心数据模型
│   ├── pipeline.py              # 分析流水线调度
│   │
│   ├── capture/                 # 事件捕获层
│   │   ├── watcher.py           # 文件系统监控器
│   │   └── snapshot.py          # 快照管理器
│   │
│   ├── analyzers/               # 分析器集合
│   │   ├── base.py              # 抽象基类
│   │   ├── sensitive_path.py    # 敏感路径策略
│   │   ├── entropy.py           # 熵值分析器
│   │   ├── frequency.py         # 频率分析器
│   │   ├── honeypot.py          # 蜜罐哨兵
│   │   ├── hash_diff.py         # 哈希比对器
│   │   └── fuzzy_hash.py        # 模糊哈希分析器
│   │
│   ├── scoring/                 # 风险评估层
│   │   ├── scorer.py            # 评分引擎
│   │   └── alert.py             # 告警管理器
│   │
│   └── output/                  # 展示层
│       ├── dashboard.py         # CLI 实时面板
│       ├── logger.py            # JSON Lines 日志
│       └── report.py            # HTML 报告生成
│
├── templates/
│   └── report.html              # Jinja2 报告模板
│
├── tests/                       # 单元测试
│   ├── test_entropy.py
│   ├── test_frequency.py
│   ├── test_scorer.py
│   └── test_snapshot.py
│
└── experiments/                 # 实验脚本
    ├── simulate_normal.py       # 正常操作模拟
    ├── simulate_ransomware.py   # 勒索软件行为模拟
    ├── simulate_sensitive.py    # 敏感文件访问模拟
    └── sandbox/                 # 实验沙箱目录
        ├── documents/
        ├── financial/
        └── config/
```

## 配置说明

配置文件 `config.yaml` 的主要配置项：

| 配置段 | 说明 |
|--------|------|
| `fileguard.watch_dirs` | 监控目录列表 |
| `fileguard.exclude_patterns` | 排除的文件模式 |
| `fileguard.analyzers.*` | 各分析器的启用开关、权重和阈值 |
| `fileguard.scoring.levels` | 风险等级评分区间 |
| `fileguard.snapshot` | 快照备份配置（备份目录、文件大小上限等） |
| `fileguard.output` | 输出配置（日志文件路径、报告路径、面板刷新频率） |
| `fileguard.general` | 通用配置（事件去抖间隔、队列大小上限） |

## 许可证

MIT
