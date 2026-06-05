import { BarChart, Card, EmptyState, LevelBadge, PathText, ScoreSparkline, StatCard, formatTime, relativeTime } from "../components/common";
import type { DashboardData } from "../types";

export function OverviewView({ data, onOpenAlerts }: { data: DashboardData; onOpenAlerts: () => void }) {
  const latestAlert = data.alerts.alerts[0] ?? null;
  const levelRows = Object.entries(data.alerts.by_level).map(([label, value]) => ({
    label,
    value,
    className: `level-${label.toLowerCase()}`,
  }));
  const eventTypeCounts = data.events.events.reduce<Record<string, number>>((acc, event) => {
    acc[event.event_type] = (acc[event.event_type] ?? 0) + 1;
    return acc;
  }, {});
  const scorePoints = data.alerts.alerts.slice().reverse().map((alert) => alert.score);

  return (
    <div className="view-stack">
      <div className="stat-grid">
        <StatCard label="Monitor" value={data.status.running ? "运行中" : "未运行"} hint={`${Math.round(data.status.uptime_seconds)}s`} />
        <StatCard label="事件总数" value={data.status.events_total.toLocaleString()} hint={`队列 ${data.status.queue_size}`} />
        <StatCard label="告警总数" value={data.status.alerts_total.toLocaleString()} hint={`最近 ${relativeTime(data.status.last_alert_time) || "-"}`} />
        <StatCard label="最高风险" value={<LevelBadge level={data.status.highest_level} />} hint={`分析器 ${data.status.analyzers_enabled}`} />
        <StatCard label="快照" value={data.status.snapshot_available ? "可用" : "无"} hint={data.snapshots.files_total ? `${data.snapshots.files_total} 文件` : "-"} />
        <StatCard label="报告" value={data.status.report_available ? "已生成" : "未生成"} hint={data.reports.generated_at ? formatTime(data.reports.generated_at) : "-"} />
      </div>

      <div className="layout-two">
        <Card title="风险等级分布">
          <BarChart rows={levelRows} />
        </Card>
        <Card title="评分时间趋势">
          <ScoreSparkline points={scorePoints} />
        </Card>
      </div>

      <div className="layout-two">
        <Card title="事件类型分布">
          <BarChart rows={Object.entries(eventTypeCounts).map(([label, value]) => ({ label, value }))} />
        </Card>
        <Card title="分析器触发次数">
          <BarChart rows={data.analyzers.items.map((item) => ({ label: item.name, value: item.signals_total }))} />
        </Card>
      </div>

      <Card title="最近告警" actions={<button className="text-button" onClick={onOpenAlerts}>查看全部</button>}>
        {latestAlert ? (
          <div className="alert-preview">
            <LevelBadge level={latestAlert.level} />
            <strong>{latestAlert.score.toFixed(2)}</strong>
            <PathText path={latestAlert.src_path} />
            <span>{latestAlert.signal_types.join(", ") || "-"}</span>
            <small>{formatTime(latestAlert.timestamp)}</small>
          </div>
        ) : (
          <EmptyState text="暂无告警" />
        )}
      </Card>
    </div>
  );
}
