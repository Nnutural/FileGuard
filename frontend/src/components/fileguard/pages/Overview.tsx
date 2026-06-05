import { useMemo, useState } from "react";
import {
  StatCard,
  ContentCard,
  RiskBadge,
  StatusDot,
  PathCell,
  Chip,
  GhostLink,
  EmptyState,
} from "../atoms";
import {
  formatScore,
  formatTime,
  formatUptime,
} from "../data";
import type { AlertItem, DashboardData, RiskLevel } from "../data";
import {
  Activity,
  AlertTriangle,
  Archive,
  ChevronRight,
  FileText,
  Inbox,
  ListChecks,
  ShieldCheck,
} from "lucide-react";
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  LabelList,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DetailDrawer } from "../Drawer";
import { AlertDetailBody } from "./Alerts";
import type { PageKey } from "../Sidebar";

const RISK_PALETTE: Record<RiskLevel, string> = {
  LOW: "#009E73",
  MEDIUM: "#E69F00",
  HIGH: "#D55E00",
  CRITICAL: "#CC3311",
  UNKNOWN: "#7A869A",
};

const EVENT_TYPE_PALETTE: Record<string, string> = {
  created: "#0072B2",
  modified: "#56B4E9",
  deleted: "#D55E00",
  renamed: "#CC79A7",
  moved: "#7A869A",
};

const ANALYZER_PALETTE: Record<string, string> = {
  HashDiffChecker: "#0072B2",
  SensitivePath: "#009E73",
  Entropy: "#E69F00",
  Frequency: "#56B4E9",
  FuzzyHash: "#CC79A7",
  HoneypotSentinel: "#D55E00",
  Honeypot: "#D55E00",
};

type ChartPayload = {
  color?: string;
  dataKey?: string | number;
  value?: string | number;
  payload?: { fill?: string };
};

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: ChartPayload[];
  label?: string | number;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="fg-tooltip">
      <div className="label">{label}</div>
      {payload.map((item, index) => (
        <div key={index} className="value flex items-center gap-2">
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: 2,
              background: item.color || item.payload?.fill || "#0072B2",
              display: "inline-block",
              flexShrink: 0,
            }}
          />
          <span style={{ color: "var(--fg-text-2)" }}>{item.dataKey}</span>
          <span className="fg-num" style={{ marginLeft: "auto", fontWeight: 600, color: "var(--fg-text)" }}>
            {item.value}
          </span>
        </div>
      ))}
    </div>
  );
}

const AXIS_PROPS = {
  stroke: "#94A3B8",
  fontSize: 11,
  tickLine: false,
  axisLine: { stroke: "#CBD5E1", strokeWidth: 1 },
} as const;

const GRID_PROPS = {
  strokeDasharray: "2 4",
  stroke: "#E2E8F0",
} as const;

function shortAnalyzerName(name: string): string {
  return name.replace("Analyzer", "").replace("Sentinel", "");
}

function AlertFeedItem({
  alert,
  onClick,
  last,
}: {
  alert: AlertItem;
  onClick: () => void;
  last: boolean;
}) {
  return (
    <div
      onClick={onClick}
      className="flex items-center gap-3 px-5 py-3 cursor-pointer transition-colors"
      style={{
        borderBottom: last ? "none" : "1px solid var(--fg-border-soft)",
        position: "relative",
      }}
      onMouseEnter={(event) => {
        event.currentTarget.style.background = "var(--fg-row-hover)";
      }}
      onMouseLeave={(event) => {
        event.currentTarget.style.background = "transparent";
      }}
    >
      <RiskBadge level={alert.level} />
      <span className="fg-num" style={{ fontSize: 13, color: "var(--fg-text)", minWidth: 38, fontWeight: 600 }}>
        {formatScore(alert.score)}
      </span>
      <div className="flex-1 min-w-0">
        <PathCell path={alert.src_path} max={44} />
        <div className="flex gap-1 flex-wrap mt-1">
          {alert.signal_types.slice(0, 3).map((signal) => (
            <Chip key={signal} color="#1E3A8A" bg="#EAF1FF" border="#C7D8FF" mono>
              {signal}
            </Chip>
          ))}
        </div>
      </div>
      <div className="hidden md:flex flex-col items-end">
        <span className="fg-num fg-mono" style={{ fontSize: 11, color: "var(--fg-text-2)" }}>
          {formatTime(alert.timestamp)}
        </span>
        {alert.escalated && <span style={{ fontSize: 10.5, color: "#9A3412", marginTop: 2 }}>↑ 已升级</span>}
      </div>
      <ChevronRight size={14} style={{ color: "var(--fg-text-3)" }} />
    </div>
  );
}

export function Overview({ data, onGoto }: { data: DashboardData; onGoto: (page: PageKey) => void }) {
  const [openAlert, setOpenAlert] = useState<AlertItem | null>(null);
  const riskDist = useMemo(
    () =>
      (["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const).map((name) => ({
        name,
        value: data.alerts.by_level[name],
        fill: RISK_PALETTE[name],
      })),
    [data.alerts.by_level],
  );
  const scoreTrend = useMemo(() => {
    const eventScores = data.events.events
      .slice()
      .reverse()
      .filter((event) => event.score !== null)
      .map((event, index) => ({ idx: index + 1, score: event.score ?? 0 }));
    if (eventScores.length > 0) return eventScores;
    return data.alerts.alerts
      .slice()
      .reverse()
      .map((alert, index) => ({ idx: index + 1, score: alert.score }));
  }, [data.alerts.alerts, data.events.events]);
  const eventTypeDist = useMemo(() => {
    const counts = data.events.events.reduce<Record<string, number>>((acc, event) => {
      acc[event.event_type] = (acc[event.event_type] ?? 0) + 1;
      return acc;
    }, {});
    return Object.entries(counts).map(([name, value]) => ({
      name,
      value,
      fill: EVENT_TYPE_PALETTE[name] ?? "#7A869A",
    }));
  }, [data.events.events]);
  const analyzerDist = useMemo(
    () =>
      data.analyzers.items
        .map((analyzer) => {
          const short = shortAnalyzerName(analyzer.name);
          return {
            name: short,
            full: analyzer.name,
            value: analyzer.signals_total,
            fill: ANALYZER_PALETTE[short] ?? ANALYZER_PALETTE[analyzer.name] ?? "#7A869A",
          };
        })
        .sort((a, b) => b.value - a.value),
    [data.analyzers.items],
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard
          label="Monitor 状态"
          value={
            <div className="flex items-center gap-2">
              <StatusDot on={data.status.running} pulse />
              <span style={{ fontSize: 18, fontWeight: 600 }}>{data.status.running ? "running" : "stopped"}</span>
            </div>
          }
          sub={<span className="fg-mono fg-num">uptime {formatUptime(data.status.uptime_seconds)}</span>}
          icon={<Activity size={13} />}
        />
        <StatCard
          label="事件总数"
          value={data.status.events_total.toLocaleString()}
          sub={
            <>
              已处理 <span className="fg-num">{data.status.events_processed.toLocaleString()}</span>
            </>
          }
          icon={<ListChecks size={13} />}
        />
        <StatCard
          label="告警总数"
          value={data.status.alerts_total.toLocaleString()}
          sub={<span className="fg-mono fg-num">最近 {formatTime(data.status.last_alert_time)}</span>}
          icon={<AlertTriangle size={13} />}
        />
        <StatCard
          label="最高风险"
          value={<RiskBadge level={data.status.highest_level} />}
          sub={`分析器 ${data.status.analyzers_enabled}`}
          icon={<ShieldCheck size={13} />}
        />
        <StatCard
          label="快照状态"
          value={data.status.snapshot_available ? "可用" : "未启用"}
          sub={data.snapshots.files_total ? `${data.snapshots.files_total.toLocaleString()} files` : "baseline / backup"}
          icon={<Archive size={13} />}
        />
        <StatCard
          label="报告状态"
          value={data.status.report_available ? "可用" : "未生成"}
          sub={formatTime(data.reports.generated_at)}
          icon={<FileText size={13} />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ContentCard
          title="风险等级分布"
          subtitle="按最近告警聚合"
          extra={<span className="fg-mono" style={{ fontSize: 11, color: "var(--fg-text-3)" }}>n={data.alerts.total}</span>}
        >
          <div style={{ height: 240 }}>
            <ResponsiveContainer>
              <BarChart data={riskDist} margin={{ top: 18, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid {...GRID_PROPS} vertical={false} />
                <XAxis dataKey="name" {...AXIS_PROPS} />
                <YAxis {...AXIS_PROPS} axisLine={false} width={32} />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(15, 23, 42, 0.03)" }} />
                <Bar dataKey="value" radius={[3, 3, 0, 0]} maxBarSize={36}>
                  {riskDist.map((row) => <Cell key={row.name} fill={row.fill} />)}
                  <LabelList dataKey="value" position="top" style={{ fill: "var(--fg-text-2)", fontSize: 11, fontFamily: "var(--fg-font-mono)" }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ContentCard>

        <ContentCard title="评分时间趋势" subtitle="最近事件 score 序列" extra={<span className="fg-mono" style={{ fontSize: 11, color: "var(--fg-text-3)" }}>score 0–10</span>}>
          <div style={{ height: 240 }}>
            <ResponsiveContainer>
              <ComposedChart data={scoreTrend} margin={{ top: 10, right: 16, left: -16, bottom: 0 }}>
                <defs>
                  <linearGradient id="fg-score-fill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0072B2" stopOpacity={0.07} />
                    <stop offset="100%" stopColor="#0072B2" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid {...GRID_PROPS} vertical={false} />
                <XAxis dataKey="idx" {...AXIS_PROPS} />
                <YAxis {...AXIS_PROPS} axisLine={false} domain={[0, 10]} width={32} />
                <Tooltip content={<ChartTooltip />} cursor={{ stroke: "#CBD5E1", strokeDasharray: "2 4" }} />
                <Area type="monotone" dataKey="score" fill="url(#fg-score-fill)" stroke="none" isAnimationActive={false} />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#0072B2"
                  strokeWidth={2}
                  dot={{ r: 3, fill: "white", stroke: "#0072B2", strokeWidth: 1.5 }}
                  activeDot={{ r: 5, fill: "#0072B2", stroke: "white", strokeWidth: 2 }}
                  isAnimationActive
                  animationDuration={600}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </ContentCard>

        <ContentCard title="事件类型分布" subtitle="近端文件事件">
          <div style={{ height: 240 }}>
            {eventTypeDist.length === 0 ? (
              <EmptyState title="暂无事件分布" desc="后端尚未返回事件记录。" icon={<Inbox size={20} />} />
            ) : (
              <ResponsiveContainer>
                <BarChart data={eventTypeDist} margin={{ top: 18, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid {...GRID_PROPS} vertical={false} />
                  <XAxis dataKey="name" {...AXIS_PROPS} />
                  <YAxis {...AXIS_PROPS} axisLine={false} width={32} />
                  <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(15, 23, 42, 0.03)" }} />
                  <Bar dataKey="value" radius={[3, 3, 0, 0]} maxBarSize={32}>
                    {eventTypeDist.map((row) => <Cell key={row.name} fill={row.fill} />)}
                    <LabelList dataKey="value" position="top" style={{ fill: "var(--fg-text-2)", fontSize: 11, fontFamily: "var(--fg-font-mono)" }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </ContentCard>

        <ContentCard title="分析器触发次数" subtitle="signals_total 排行">
          <div style={{ height: 240 }}>
            <ResponsiveContainer>
              <BarChart data={analyzerDist} layout="vertical" margin={{ top: 4, right: 32, left: -4, bottom: 0 }}>
                <CartesianGrid {...GRID_PROPS} horizontal={false} />
                <XAxis type="number" {...AXIS_PROPS} axisLine={false} />
                <YAxis dataKey="name" type="category" stroke="#475569" fontSize={11} tickLine={false} axisLine={false} width={104} />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(15, 23, 42, 0.03)" }} />
                <Bar dataKey="value" radius={[0, 3, 3, 0]} maxBarSize={14}>
                  {analyzerDist.map((row) => <Cell key={row.full} fill={row.fill} />)}
                  <LabelList dataKey="value" position="right" style={{ fill: "var(--fg-text-2)", fontSize: 11, fontFamily: "var(--fg-font-mono)" }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ContentCard>
      </div>

      <ContentCard
        title="最近告警"
        subtitle="alert feed · 最近 5 条"
        extra={<GhostLink onClick={() => onGoto("alerts")} icon={<ChevronRight size={13} />}>查看全部</GhostLink>}
        padding={false}
      >
        {data.alerts.alerts.length === 0 ? (
          <EmptyState title="暂无告警" desc="当前时间线中没有告警记录。" icon={<ShieldCheck size={20} />} />
        ) : (
          data.alerts.alerts.slice(0, 5).map((alert, index) => (
            <AlertFeedItem
              key={`${alert.timestamp}-${alert.src_path}`}
              alert={alert}
              onClick={() => setOpenAlert(alert)}
              last={index === Math.min(4, data.alerts.alerts.length - 1)}
            />
          ))
        )}
      </ContentCard>

      <DetailDrawer
        open={!!openAlert}
        onClose={() => setOpenAlert(null)}
        title="告警详情"
        subtitle={openAlert && <span>alert · {formatTime(openAlert.timestamp)}</span>}
      >
        {openAlert && <AlertDetailBody alert={openAlert} />}
      </DetailDrawer>
    </div>
  );
}
