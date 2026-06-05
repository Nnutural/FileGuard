import type {
  AlertItem,
  AnalyzerItem,
  DashboardData,
  EventItem,
  EventsResponse,
  ReportStatusResponse,
  RiskLevel as ApiRiskLevel,
  SnapshotsResponse,
  Status,
} from "../../types";

export type RiskLevel = ApiRiskLevel | "UNKNOWN";

export type {
  AlertItem,
  AnalyzerItem,
  DashboardData,
  EventItem,
  EventsResponse,
  ReportStatusResponse,
  SnapshotsResponse,
  Status,
};

export const RISK_COLORS: Record<RiskLevel, { fg: string; bg: string; label: string }> = {
  LOW: { fg: "#009E73", bg: "#E6F5EF", label: "LOW" },
  MEDIUM: { fg: "#B47600", bg: "#FBF1DD", label: "MEDIUM" },
  HIGH: { fg: "#B85000", bg: "#FBE9DA", label: "HIGH" },
  CRITICAL: { fg: "#B5291A", bg: "#FBE3DF", label: "CRITICAL" },
  UNKNOWN: { fg: "#6B7280", bg: "#F3F4F6", label: "UNKNOWN" },
};

const LEVEL_ORDER: Record<RiskLevel, number> = {
  UNKNOWN: 0,
  LOW: 1,
  MEDIUM: 2,
  HIGH: 3,
  CRITICAL: 4,
};

export function normalizeLevel(level: ApiRiskLevel | null | undefined): RiskLevel {
  return level ?? "UNKNOWN";
}

export function compareRiskLevels(a: RiskLevel, b: RiskLevel): number {
  return LEVEL_ORDER[a] - LEVEL_ORDER[b];
}

export function scoreToPercent(score: number | null | undefined): number {
  if (typeof score !== "number" || Number.isNaN(score)) return 0;
  return Math.max(0, Math.min(10, score)) * 10;
}

export function scoreToLevel(score: number | null | undefined): RiskLevel {
  if (typeof score !== "number" || Number.isNaN(score)) return "UNKNOWN";
  if (score >= 8) return "CRITICAL";
  if (score >= 6) return "HIGH";
  if (score >= 3) return "MEDIUM";
  return "LOW";
}

export function formatScore(score: number | null | undefined): string {
  return typeof score === "number" && !Number.isNaN(score) ? score.toFixed(2) : "—";
}

export function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${h}h ${m}m ${s}s`;
}

export function formatBytes(value: number | null): string {
  if (value === null) return "—";
  if (value === 0) return "0 B";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(2)} MB`;
}

export function formatTime(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value.replace("T", " ");
  return date.toLocaleString();
}

export function relativeTime(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return formatTime(value);
  const seconds = Math.max(0, Math.round((Date.now() - date.getTime()) / 1000));
  if (seconds < 60) return `${seconds}s 前`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m 前`;
  return `${Math.round(minutes / 60)}h 前`;
}

export function truncatePath(path: string, max = 56): string {
  if (!path || path.length <= max) return path;
  const head = path.slice(0, Math.floor(max / 2) - 2);
  const tail = path.slice(path.length - Math.floor(max / 2) + 2);
  return `${head}…${tail}`;
}

export function recordValue(record: Record<string, unknown>, key: string): string | null {
  const value = record[key];
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return null;
}
