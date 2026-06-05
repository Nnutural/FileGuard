import type { ReactNode } from "react";
import type { RiskLevel } from "../types";

const levelLabels: Record<RiskLevel, string> = {
  LOW: "低",
  MEDIUM: "中",
  HIGH: "高",
  CRITICAL: "严重",
};

export function LevelBadge({ level }: { level: RiskLevel | null }) {
  if (!level) return <span className="badge muted">无</span>;
  return <span className={`badge level-${level.toLowerCase()}`}>{levelLabels[level]} / {level}</span>;
}

export function StatusBadge({ ok, children }: { ok: boolean; children: ReactNode }) {
  return <span className={`badge ${ok ? "ok" : "muted"}`}>{children}</span>;
}

export function Card({ title, children, actions }: { title: string; children: ReactNode; actions?: ReactNode }) {
  return (
    <section className="card">
      <div className="card-header">
        <h2>{title}</h2>
        {actions ? <div className="card-actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}

export function StatCard({ label, value, hint }: { label: string; value: ReactNode; hint?: ReactNode }) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <small>{hint}</small> : null}
    </div>
  );
}

export function EmptyState({ text }: { text: string }) {
  return <div className="empty-state">{text}</div>;
}

export function ErrorBanner({ message }: { message: string | null }) {
  if (!message) return null;
  return <div className="error-banner">{message}</div>;
}

export function SkeletonRows({ rows = 4 }: { rows?: number }) {
  return (
    <div className="skeleton-list">
      {Array.from({ length: rows }).map((_, index) => (
        <div className="skeleton-row" key={index} />
      ))}
    </div>
  );
}

export function PathText({ path }: { path: string | null }) {
  if (!path) return <span className="muted-text">-</span>;
  return <span className="path-text" title={path}>{path}</span>;
}

export function Drawer({
  title,
  open,
  children,
  onClose,
}: {
  title: string;
  open: boolean;
  children: ReactNode;
  onClose: () => void;
}) {
  if (!open) return null;
  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(event) => event.stopPropagation()}>
        <div className="drawer-header">
          <h2>{title}</h2>
          <button className="icon-button" onClick={onClose} aria-label="关闭详情">×</button>
        </div>
        {children}
      </aside>
    </div>
  );
}

export function BarChart({
  rows,
}: {
  rows: Array<{ label: string; value: number; className?: string }>;
}) {
  const max = Math.max(1, ...rows.map((row) => row.value));
  return (
    <div className="bar-chart">
      {rows.map((row) => (
        <div className="bar-row" key={row.label}>
          <span>{row.label}</span>
          <div className="bar-track">
            <div className={`bar-fill ${row.className ?? ""}`} style={{ width: `${(row.value / max) * 100}%` }} />
          </div>
          <strong>{row.value}</strong>
        </div>
      ))}
    </div>
  );
}

export function ScoreSparkline({ points }: { points: number[] }) {
  if (points.length === 0) return <EmptyState text="暂无评分趋势" />;
  const width = 360;
  const height = 120;
  const step = points.length > 1 ? width / (points.length - 1) : width;
  const path = points
    .map((score, index) => {
      const x = index * step;
      const y = height - (Math.max(0, Math.min(10, score)) / 10) * height;
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    })
    .join(" ");
  return (
    <svg className="sparkline" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="评分趋势">
      <path d={path} />
    </svg>
  );
}

export function formatBytes(value: number | null): string {
  if (value === null) return "-";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

export function formatTime(value: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function relativeTime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  const seconds = Math.max(0, Math.round((Date.now() - date.getTime()) / 1000));
  if (seconds < 60) return `${seconds}s 前`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m 前`;
  return `${Math.round(minutes / 60)}h 前`;
}
