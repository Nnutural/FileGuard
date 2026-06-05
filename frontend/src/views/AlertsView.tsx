import { useMemo, useState } from "react";
import { Card, Drawer, EmptyState, LevelBadge, PathText, formatTime, relativeTime } from "../components/common";
import type { AlertItem, AlertsResponse, RiskLevel } from "../types";

type AlertSortKey = "timestamp" | "score" | "level";

export function AlertsView({ alerts }: { alerts: AlertsResponse }) {
  const [level, setLevel] = useState<RiskLevel | "all">("all");
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<AlertSortKey>("timestamp");
  const [selected, setSelected] = useState<AlertItem | null>(null);

  const filtered = useMemo(() => {
    const rows = alerts.alerts.filter((alert) => {
      const matchesLevel = level === "all" || alert.level === level;
      const path = `${alert.src_path} ${alert.dest_path ?? ""}`.toLowerCase();
      return matchesLevel && path.includes(query.toLowerCase());
    });
    return rows.sort((a, b) => {
      if (sortKey === "timestamp") return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      if (sortKey === "score") return b.score - a.score;
      return b.level.localeCompare(a.level);
    });
  }, [alerts.alerts, level, query, sortKey]);

  return (
    <Card title="告警中心">
      <div className="toolbar">
        <select value={level} onChange={(event) => setLevel(event.target.value as RiskLevel | "all")}>
          <option value="all">全部等级</option>
          <option value="LOW">LOW</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="HIGH">HIGH</option>
          <option value="CRITICAL">CRITICAL</option>
        </select>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索告警路径" />
        <select value={sortKey} onChange={(event) => setSortKey(event.target.value as AlertSortKey)}>
          <option value="timestamp">按时间</option>
          <option value="score">按分数</option>
          <option value="level">按等级</option>
        </select>
      </div>
      {filtered.length === 0 ? <EmptyState text="没有匹配的告警" /> : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>等级</th>
                <th>分数</th>
                <th>路径</th>
                <th>信号</th>
                <th>升级</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 100).map((alert) => (
                <tr key={`${alert.timestamp}-${alert.src_path}`} onClick={() => setSelected(alert)}>
                  <td><LevelBadge level={alert.level} /></td>
                  <td>{alert.score.toFixed(2)}</td>
                  <td><PathText path={alert.src_path} /></td>
                  <td>{alert.signal_types.join(", ") || "-"}</td>
                  <td>{alert.escalated ? "是" : "否"}</td>
                  <td title={formatTime(alert.timestamp)}>{relativeTime(alert.timestamp)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Drawer title="告警详情" open={selected !== null} onClose={() => setSelected(null)}>
        {selected ? (
          <div className="detail-stack">
            <div className="detail-line"><LevelBadge level={selected.level} /><strong>{selected.score.toFixed(2)}</strong></div>
            <PathText path={selected.src_path} />
            {selected.escalated ? <p className="notice">升级原因：{selected.escalation_reason}</p> : null}
            <h3>Signals</h3>
            {selected.signals.map((signal) => (
              <div className="signal-box" key={`${signal.timestamp}-${signal.signal_type}`}>
                <strong>{signal.analyzer_name}</strong>
                <span>{signal.signal_type} / value {signal.value.toFixed(2)} / weight {signal.weight.toFixed(2)}</span>
                <pre className="json-block">{JSON.stringify(signal.evidence, null, 2)}</pre>
              </div>
            ))}
          </div>
        ) : null}
      </Drawer>
    </Card>
  );
}
