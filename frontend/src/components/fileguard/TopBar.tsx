import { ReactNode, useState } from "react";
import { RefreshCw, Radio, Database, ShieldAlert, Clock } from "lucide-react";
import { RiskBadge } from "./atoms";
import { formatTime, Status } from "./data";
import type { ConnectionMode, DataMode } from "../../types";

export function StatusChip({
  tone = "mute",
  icon,
  label,
  value,
  pulse,
}: {
  tone?: "ok" | "warn" | "info" | "mute" | "danger";
  icon?: ReactNode;
  label: string;
  value?: ReactNode;
  pulse?: boolean;
}) {
  const dataTone = tone === "danger" ? "warn" : tone;
  return (
    <span className="fg-chip" data-tone={dataTone}>
      {icon ? (
        <span style={{ display: "inline-flex", alignItems: "center" }}>{icon}</span>
      ) : (
        <span className={"fg-chip-dot " + (pulse ? "fg-pulse-dot" : "")} />
      )}
      <span style={{ fontWeight: 500 }}>{label}</span>
      {value !== undefined && (
        <>
          <span style={{ width: 1, height: 10, background: "currentColor", opacity: 0.25 }} />
          <span className="fg-num">{value}</span>
        </>
      )}
    </span>
  );
}

export function TopBar({
  status,
  dataMode,
  connectionMode,
  autoRefresh,
  lastUpdated,
  onRefresh,
  onAutoRefreshChange,
}: {
  status: Status;
  dataMode: DataMode;
  connectionMode: ConnectionMode;
  autoRefresh: boolean;
  lastUpdated: string | null;
  onRefresh: () => Promise<void>;
  onAutoRefreshChange: (enabled: boolean) => void;
}) {
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      await onRefresh();
    } finally {
      setLoading(false);
    }
  }

  return (
    <header
      className="fg-card flex items-center justify-between px-5 flex-wrap gap-3"
      style={{ minHeight: 64, paddingTop: 10, paddingBottom: 10 }}
    >
      <div>
        <div className="flex items-center gap-2">
          <h1
            style={{
              color: "var(--fg-text)",
              fontSize: 17,
              fontWeight: 600,
              lineHeight: "22px",
              letterSpacing: "0.005em",
            }}
          >
            文件安全风险感知控制台
          </h1>
          <span
            className="fg-mono"
            style={{
              fontSize: 10,
              padding: "1px 6px",
              borderRadius: 4,
              border: "1px solid var(--fg-border)",
              background: "#F8FAFC",
              color: "var(--fg-text-2)",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
            }}
          >
            v0.1.0
          </span>
        </div>
        <div className="flex items-center gap-1.5" style={{ color: "var(--fg-text-2)", fontSize: 12, marginTop: 3 }}>
          <span>感知</span>
          <Dot />
          <span>分析</span>
          <Dot />
          <span>响应</span>
          <Dot />
          <span>展示</span>
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <StatusChip
          tone={status.running ? "ok" : "mute"}
          label={status.running ? "Monitor 运行" : "Monitor 停止"}
          pulse={status.running}
        />
        <StatusChip
          tone={dataMode === "api" ? "ok" : "warn"}
          icon={<Database size={12} />}
          label={dataMode === "api" ? "真实 API" : "Demo data mode"}
        />
        <StatusChip
          tone={connectionMode === "realtime" ? "ok" : connectionMode === "polling" ? "warn" : "mute"}
          icon={<Radio size={12} />}
          label={connectionMode === "realtime" ? "SSE 实时" : connectionMode === "polling" ? "轮询" : "离线"}
        />
        <StatusChip
          tone={autoRefresh ? "info" : "mute"}
          icon={<Clock size={12} />}
          label={autoRefresh ? "自动刷新" : "手动刷新"}
          value={formatTime(lastUpdated)}
        />
        <span className="fg-chip" data-tone="info" title={`最高风险等级 ${status.highest_level}`}>
          <ShieldAlert size={12} />
          <span style={{ fontWeight: 500 }}>最高</span>
          <span style={{ width: 1, height: 10, background: "currentColor", opacity: 0.25 }} />
          <RiskBadge level={status.highest_level} />
        </span>

        <span className="fg-divider-y" />

        <button
          onClick={() => onAutoRefreshChange(!autoRefresh)}
          className="fg-btn fg-btn-secondary"
          aria-pressed={autoRefresh}
        >
          {autoRefresh ? "暂停自动" : "启用自动"}
        </button>
        <button onClick={() => void refresh()} className="fg-btn fg-btn-secondary" disabled={loading} aria-label="刷新">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} style={{ transition: "transform var(--fg-motion-fast)" }} />
          {loading ? "刷新中" : "刷新"}
        </button>
      </div>
    </header>
  );
}

function Dot() {
  return (
    <span
      style={{
        width: 3,
        height: 3,
        borderRadius: "50%",
        background: "var(--fg-text-3)",
        display: "inline-block",
      }}
    />
  );
}
