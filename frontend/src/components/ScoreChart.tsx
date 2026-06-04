import { useEffect, useState } from "react";
import { api } from "../api/fileguard";
import type { AlertItem } from "../types";

export function ScoreChart() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);

  useEffect(() => {
    api.getAlerts().then((d) => setAlerts(d.alerts)).catch(console.error);
    const id = setInterval(() => api.getAlerts().then((d) => setAlerts(d.alerts)).catch(console.error), 5000);
    return () => clearInterval(id);
  }, []);

  const maxScore = 10;
  const recent = alerts.slice(-20);

  return (
    <div className="card">
      <h2>评分趋势</h2>
      {recent.length === 0 ? (
        <p style={{ color: "#aaa" }}>暂无数据</p>
      ) : (
        <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height: 120 }}>
          {recent.map((a, i) => (
            <div
              key={i}
              title={`${a.timestamp}\n${a.score.toFixed(2)} (${a.level})`}
              style={{
                flex: 1,
                height: `${(a.score / maxScore) * 100}%`,
                background: a.level === "CRITICAL" ? "#d63031"
                  : a.level === "HIGH" ? "#e17055"
                  : a.level === "MEDIUM" ? "#f39c12"
                  : "#00b894",
                borderRadius: "2px 2px 0 0",
                minWidth: 4,
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
