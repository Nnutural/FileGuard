import { useCallback, useEffect, useMemo, useState } from "react";
import { api, subscribeEventStream } from "../api/fileguard";
import { demoData } from "../demoData";
import type { ConnectionMode, DashboardData, DataMode, ReportStatusResponse } from "../types";

interface FileGuardState {
  data: DashboardData;
  loading: boolean;
  error: string | null;
  dataMode: DataMode;
  connectionMode: ConnectionMode;
  autoRefresh: boolean;
  lastUpdated: string | null;
  refresh: () => Promise<void>;
  setAutoRefresh: (enabled: boolean) => void;
  useDemoData: () => void;
  generateReport: () => Promise<ReportStatusResponse>;
}

export function useFileGuardData(): FileGuardState {
  const [data, setData] = useState<DashboardData>(demoData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataMode, setDataMode] = useState<DataMode>("demo");
  const [connectionMode, setConnectionMode] = useState<ConnectionMode>("offline");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const next = await api.getDashboard();
      setData(next);
      setDataMode("api");
      setConnectionMode((current) => (current === "realtime" ? "realtime" : "polling"));
      setError(null);
      setLastUpdated(new Date().toISOString());
    } catch (caught) {
      setData(demoData);
      setDataMode("demo");
      setConnectionMode("offline");
      setError(caught instanceof Error ? caught.message : "API 不可用，已切换到 Demo data mode");
      setLastUpdated(new Date().toISOString());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!autoRefresh) return undefined;
    const timer = window.setInterval(() => {
      void refresh();
    }, 5000);
    return () => window.clearInterval(timer);
  }, [autoRefresh, refresh]);

  useEffect(() => {
    if (!autoRefresh) return undefined;
    const unsubscribe = subscribeEventStream(
      () => {
        setConnectionMode("realtime");
        void refresh();
      },
      () => {
        setConnectionMode("polling");
      },
    );
    return unsubscribe;
  }, [autoRefresh, refresh]);

  const generateReport = useCallback(async () => {
    const result = await api.generateReport();
    await refresh();
    return result;
  }, [refresh]);

  const useDemoData = useCallback(() => {
    setData(demoData);
    setDataMode("demo");
    setConnectionMode("offline");
    setError(null);
    setLoading(false);
    setLastUpdated(new Date().toISOString());
  }, []);

  return useMemo(
    () => ({
      data,
      loading,
      error,
      dataMode,
      connectionMode,
      autoRefresh,
      lastUpdated,
      refresh,
      setAutoRefresh,
      useDemoData,
      generateReport,
    }),
    [
      autoRefresh,
      connectionMode,
      data,
      dataMode,
      error,
      generateReport,
      lastUpdated,
      loading,
      refresh,
      useDemoData,
    ],
  );
}
