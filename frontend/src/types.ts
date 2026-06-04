/** 系统运行状态 */
export interface Status {
  running: boolean;
  watch_dirs: string[];
  uptime_seconds: number;
  events_processed: number;
  queue_size: number;
}

/** 单条告警 */
export interface AlertItem {
  timestamp: string;
  event_type: string;
  src_path: string;
  dest_path: string | null;
  score: number;
  level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  analyzers: string[];
}

/** 告警列表响应 */
export interface AlertsResponse {
  total: number;
  alerts: AlertItem[];
}

/** 单条文件事件 */
export interface EventItem {
  timestamp: string;
  event_type: string;
  src_path: string;
  dest_path: string | null;
  file_size: number | null;
  is_directory: boolean;
}

/** 事件列表响应 */
export interface EventsResponse {
  total: number;
  events: EventItem[];
}
