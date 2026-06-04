import type { Status, AlertsResponse, EventsResponse } from "../types";

const BASE = "/api";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  getStatus: () => fetchJSON<Status>("/status"),
  getAlerts: () => fetchJSON<AlertsResponse>("/alerts"),
  getEvents: () => fetchJSON<EventsResponse>("/events"),
};
