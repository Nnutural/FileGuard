import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Bug, Fingerprint, FolderLock, Gauge, Hash, Repeat, type LucideIcon } from "lucide-react";
import { Chip, ContentCard, EmptyState, Sparkline } from "../atoms";
import { formatTime } from "../data";
import type { AnalyzerItem } from "../data";
import type { AnalyzersResponse } from "../../../types";

const ICONS: Record<string, LucideIcon> = {
  SensitivePathAnalyzer: FolderLock,
  EntropyAnalyzer: Gauge,
  FrequencyAnalyzer: Repeat,
  HoneypotSentinel: Bug,
  HashDiffChecker: Hash,
  FuzzyHashAnalyzer: Fingerprint,
};

const DESC: Record<string, string> = {
  SensitivePathAnalyzer: "敏感路径与扩展名匹配",
  EntropyAnalyzer: "文件熵值异常检测",
  FrequencyAnalyzer: "高频文件操作识别",
  HoneypotSentinel: "诱饵文件触发监听",
  HashDiffChecker: "Baseline 哈希差异比对",
  FuzzyHashAnalyzer: "模糊哈希相似度比对",
};

const ANALYZER_COLOR: Record<string, string> = {
  HashDiffChecker: "#0072B2",
  SensitivePath: "#009E73",
  Entropy: "#E69F00",
  Frequency: "#56B4E9",
  FuzzyHash: "#CC79A7",
  Honeypot: "#D55E00",
};

type ChartPayload = { value?: number; payload?: { fill?: string } };

function shortName(name: string): string {
  return name.replace("Analyzer", "").replace("Sentinel", "");
}

function colorFor(name: string): string {
  return ANALYZER_COLOR[shortName(name)] ?? ANALYZER_COLOR[name] ?? "#7A869A";
}

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: ChartPayload[]; label?: string | number }) {
  if (!active || !payload?.length) return null;
  const fill = payload[0].payload?.fill ?? "#0072B2";
  return (
    <div className="fg-tooltip">
      <div className="label">{label}</div>
      <div className="value flex items-center gap-2">
        <span style={{ width: 8, height: 8, borderRadius: 2, background: fill }} />
        <span style={{ color: "var(--fg-text-2)" }}>signals_total</span>
        <span className="fg-num" style={{ marginLeft: "auto", fontWeight: 600, color: "var(--fg-text)" }}>
          {payload[0].value}
        </span>
      </div>
    </div>
  );
}

export function Analyzers({ analyzers }: { analyzers: AnalyzersResponse }) {
  const sorted = analyzers.items.slice().sort((a, b) => b.signals_total - a.signals_total);
  const chartData = sorted.map((analyzer) => ({
    name: shortName(analyzer.name),
    value: analyzer.signals_total,
    fill: colorFor(analyzer.name),
  }));
  const enabled = analyzers.items.filter((item) => item.enabled).length;

  return (
    <div className="space-y-4">
      <ContentCard
        title="分析器触发排行"
        subtitle="按 signals_total 倒序"
        extra={<Chip mono color="#003399" bg="#EAF1FF" border="#C7D8FF">{enabled} / {analyzers.total} 启用</Chip>}
      >
        <div style={{ height: 260 }}>
          {chartData.length === 0 ? (
            <EmptyState title="暂无分析器状态" desc="后端尚未返回分析器运行状态。" icon={<Gauge size={20} />} />
          ) : (
            <ResponsiveContainer>
              <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 36, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="2 4" stroke="#E2E8F0" horizontal={false} />
                <XAxis type="number" stroke="#94A3B8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis dataKey="name" type="category" stroke="#475569" fontSize={11.5} tickLine={false} axisLine={false} width={120} />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(15, 23, 42, 0.03)" }} />
                <Bar dataKey="value" radius={[0, 3, 3, 0]} maxBarSize={14}>
                  {chartData.map((row) => <Cell key={row.name} fill={row.fill} />)}
                  <LabelList dataKey="value" position="right" style={{ fill: "var(--fg-text-2)", fontSize: 11, fontFamily: "var(--fg-font-mono)" }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </ContentCard>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sorted.map((analyzer) => <AnalyzerCard key={analyzer.name} analyzer={analyzer} />)}
      </div>
    </div>
  );
}

function AnalyzerCard({ analyzer }: { analyzer: AnalyzerItem }) {
  const Icon = ICONS[analyzer.name] ?? Hash;
  const dimmed = !analyzer.enabled;
  return (
    <div className="fg-card" style={{ padding: 16, opacity: dimmed ? 0.7 : 1 }}>
      <div className="flex items-start justify-between mb-3">
        <div
          className="flex items-center justify-center"
          style={{
            width: 34,
            height: 34,
            borderRadius: 8,
            background: analyzer.enabled ? "var(--fg-primary-soft)" : "#F1F5F9",
            color: analyzer.enabled ? "var(--fg-primary)" : "var(--fg-text-3)",
            border: "1px solid",
            borderColor: analyzer.enabled ? "#D6E2FB" : "#E2E8F0",
          }}
        >
          <Icon size={16} strokeWidth={1.75} />
        </div>
        <span className="fg-chip" data-tone={analyzer.enabled ? "ok" : "mute"} style={{ height: 22 }}>
          <span className="fg-chip-dot" />
          {analyzer.enabled ? "启用" : "禁用"}
        </span>
      </div>
      <div className="fg-mono" style={{ fontSize: 13.5, color: "var(--fg-text)", fontWeight: 600 }}>
        {analyzer.name}
      </div>
      <div style={{ color: "var(--fg-text-2)", fontSize: 12, marginTop: 2 }}>
        {DESC[analyzer.name] ?? "检测模块运行状态"}
      </div>

      <div
        className="grid grid-cols-2 mt-3"
        style={{ border: "1px solid var(--fg-border-soft)", borderRadius: 6, overflow: "hidden", background: "#FAFCFE" }}
      >
        <div style={{ padding: "8px 10px", borderRight: "1px solid var(--fg-border-soft)" }}>
          <div className="fg-mono" style={{ fontSize: 10, color: "var(--fg-text-3)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            weight
          </div>
          <div className="fg-num" style={{ fontSize: 15, color: "var(--fg-text)", fontWeight: 600 }}>
            {analyzer.weight.toFixed(2)}
          </div>
        </div>
        <div style={{ padding: "8px 10px" }}>
          <div className="fg-mono" style={{ fontSize: 10, color: "var(--fg-text-3)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            signals
          </div>
          <div className="fg-num" style={{ fontSize: 15, color: "var(--fg-text)", fontWeight: 600 }}>
            {analyzer.signals_total}
          </div>
        </div>
      </div>

      <Sparkline values={[Math.max(1, analyzer.signals_total)]} color={analyzer.enabled ? colorFor(analyzer.name) : "#94A3B8"} />

      <div className="fg-mono" style={{ color: "var(--fg-text-3)", fontSize: 11, marginTop: 10 }}>
        last_triggered_at · {formatTime(analyzer.last_triggered_at)}
      </div>
    </div>
  );
}
