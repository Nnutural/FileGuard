import { BarChart, Card, EmptyState, StatusBadge, formatTime, relativeTime } from "../components/common";
import type { AnalyzersResponse } from "../types";

export function AnalyzersView({ analyzers }: { analyzers: AnalyzersResponse }) {
  const sorted = analyzers.items.slice().sort((a, b) => b.signals_total - a.signals_total);
  return (
    <div className="view-stack">
      <Card title="分析器触发排行">
        <BarChart rows={sorted.map((item) => ({ label: item.name, value: item.signals_total }))} />
      </Card>
      <Card title="分析器状态">
        {sorted.length === 0 ? <EmptyState text="暂无分析器状态" /> : (
          <div className="analyzer-grid">
            {sorted.map((item) => (
              <article className="analyzer-card" key={item.name}>
                <div>
                  <h3>{item.name}</h3>
                  <StatusBadge ok={item.enabled}>{item.enabled ? "启用" : "禁用"}</StatusBadge>
                </div>
                <dl>
                  <dt>权重</dt>
                  <dd>{item.weight.toFixed(2)}</dd>
                  <dt>触发次数</dt>
                  <dd>{item.signals_total}</dd>
                  <dt>最近触发</dt>
                  <dd title={formatTime(item.last_triggered_at)}>{relativeTime(item.last_triggered_at) || "-"}</dd>
                </dl>
              </article>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
