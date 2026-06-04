import { useEffect, useState } from "react";
import { api } from "../api/fileguard";
import type { AlertItem } from "../types";

const levelColor: Record<string, string> = {
  CRITICAL: "#d63031",
  HIGH: "#e17055",
  MEDIUM: "#f39c12",
  LOW: "#00b894",
};

export function AlertTimeline() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);

  useEffect(() => {
    const tick = () => api.getAlerts().then((d) => setAlerts(d.alerts)).catch(console.error);
    tick();
    const id = setInterval(tick, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="card">
      <h2>告警时间线</h2>
      {alerts.length === 0 ? (
        <p style={{ color: "#aaa" }}>暂无告警</p>
      ) : (
        <ul style={{ listStyle: "none", maxHeight: 300, overflowY: "auto" }}>
          {alerts.slice(0, 50).map((a, i) => (
            <li key={i} style={{ padding: "0.3rem 0", borderBottom: "1px solid #f0f0f0" }}>
              <span style={{ color: levelColor[a.level] ?? "#333", fontWeight: "bold" }}>
                [{a.level}]
              </span>{" "}
              <span style={{ fontSize: "0.85rem", color: "#666" }}>{a.timestamp}</span>
              <br />
              {a.src_path} — {a.score.toFixed(2)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
