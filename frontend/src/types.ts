export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type DataMode = "api" | "demo";
export type ConnectionMode = "realtime" | "polling" | "offline";

export interface LevelCounts {
  LOW: number;
  MEDIUM: number;
  HIGH: number;
  CRITICAL: number;
}

export interface Status {
  running: boolean;
  watch_dirs: string[];
  uptime_seconds: number;
  events_processed: number;
  queue_size: number;
  events_total: number;
  alerts_total: number;
  highest_level: RiskLevel;
  last_event_time: string | null;
  last_alert_time: string | null;
  analyzers_enabled: number;
  snapshot_available: boolean;
  report_available: boolean;
}

export interface SignalItem {
  analyzer_name: string;
  signal_type: string;
  value: number;
  weight: number;
  evidence: Record<string, unknown>;
  timestamp: string;
}

export interface AlertItem {
  timestamp: string;
  event_type: string;
  src_path: string;
  dest_path: string | null;
  score: number;
  level: RiskLevel;
  analyzers: string[];
  signal_types: string[];
  signals: SignalItem[];
  escalated: boolean;
  escalation_reason: string | null;
}

export interface AlertsResponse {
  total: number;
  alerts: AlertItem[];
  by_level: LevelCounts;
}

export interface EventItem {
  timestamp: string;
  event_type: string;
  src_path: string;
  dest_path: string | null;
  file_size: number | null;
  is_directory: boolean;
  score: number | null;
  level: RiskLevel | null;
  signals_count: number;
}

export interface EventsResponse {
  total: number;
  events: EventItem[];
}

export interface AnalyzerItem {
  name: string;
  enabled: boolean;
  weight: number;
  signals_total: number;
  last_triggered_at: string | null;
}

export interface AnalyzersResponse {
  total: number;
  items: AnalyzerItem[];
}

export interface IncrementalSnapshotItem {
  path: string;
  old_hash: string | null;
  new_hash: string | null;
  old_entropy: number | null;
  new_entropy: number | null;
  timestamp: string;
  event_type: string;
}

export interface SnapshotsResponse {
  enabled: boolean;
  baseline_file: string | null;
  backup_dir: string | null;
  files_total: number;
  last_snapshot_time: string | null;
  last_restore_verified: boolean | null;
  incremental_total: number;
  incremental_records: IncrementalSnapshotItem[];
  auto_restore_actions: Record<string, unknown>[];
}

export interface ReportStatusResponse {
  ok: boolean;
  report_file: string;
  available: boolean;
  generated_at: string | null;
  events_total: number;
  alerts_total: number;
  error: string | null;
}

export interface DashboardData {
  status: Status;
  alerts: AlertsResponse;
  events: EventsResponse;
  analyzers: AnalyzersResponse;
  snapshots: SnapshotsResponse;
  reports: ReportStatusResponse;
}
