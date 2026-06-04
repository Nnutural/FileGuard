import { useEffect, useState } from "react";
import { api } from "../api/fileguard";
import type { AlertsResponse } from "../types";

export function RiskSummary() {
  const [data, setData] = useState<AlertsResponse | null>(null);

  useEffect(() => {
    api.getAlerts().then(setData).catch(console.error);
    const id = setInterval(() => api.getAlerts().then(setData).catch(console.error), 5000);
    return () => clearInterval(id);
  }, []);

  if (!data) return <div className="card"><h2>风险等级分布</h2><p>加载中...</p></div>;

  const counts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
  for (const a of data.alerts) {
    if (a.level in counts) counts[a.level]++;
  }

  return (
    <div className="card">
      <h2>风险等级分布</h2>
      <p>严重: {counts.CRITICAL}</p>
      <p>高危: {counts.HIGH}</p>
      <p>中危: {counts.MEDIUM}</p>
      <p>低危: {counts.LOW}</p>
      <p style={{ marginTop: "0.5rem", color: "#888" }}>共 {data.total} 条告警</p>
    </div>
  );
}
