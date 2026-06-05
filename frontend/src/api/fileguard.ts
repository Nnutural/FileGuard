import type {
  AlertsResponse,
  AnalyzersResponse,
  DashboardData,
  EventsResponse,
  ReportStatusResponse,
  SnapshotsResponse,
  Status,
} from "../types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

function endpoint(path: string): string {
  return `${API_BASE}/api${path}`;
}

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(endpoint(path), init);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`API ${path} returned ${response.status}: ${message || response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  getStatus: () => fetchJSON<Status>("/status"),
  getAlerts: () => fetchJSON<AlertsResponse>("/alerts"),
  getEvents: () => fetchJSON<EventsResponse>("/events"),
  getAnalyzers: () => fetchJSON<AnalyzersResponse>("/analyzers"),
  getSnapshots: () => fetchJSON<SnapshotsResponse>("/snapshots"),
  getReports: () => fetchJSON<ReportStatusResponse>("/reports"),
  generateReport: () => fetchJSON<ReportStatusResponse>("/reports", { method: "POST" }),
  getDashboard: async (): Promise<DashboardData> => {
    const [status, alerts, events, analyzers, snapshots, reports] = await Promise.all([
      api.getStatus(),
      api.getAlerts(),
      api.getEvents(),
      api.getAnalyzers(),
      api.getSnapshots(),
      api.getReports(),
    ]);
    return { status, alerts, events, analyzers, snapshots, reports };
  },
};

export function subscribeEventStream(onMessage: () => void, onError: () => void): () => void {
  if (!("EventSource" in window)) {
    onError();
    return () => undefined;
  }
  const source = new EventSource(endpoint("/stream"));
  const refresh = () => onMessage();
  source.addEventListener("status", refresh);
  source.addEventListener("event", refresh);
  source.addEventListener("alert", refresh);
  source.onerror = () => {
    onError();
    source.close();
  };
  return () => source.close();
}
