import { ErrorBanner, LevelBadge, SkeletonRows, StatusBadge, formatTime } from "./components/common";
import { useFileGuardData } from "./hooks/useFileGuardData";
import { AlertsView } from "./views/AlertsView";
import { AnalyzersView } from "./views/AnalyzersView";
import { DemoView } from "./views/DemoView";
import { EventsView } from "./views/EventsView";
import { OverviewView } from "./views/OverviewView";
import { ReportsView } from "./views/ReportsView";
import { SnapshotsView } from "./views/SnapshotsView";
import { useState } from "react";

type ViewId = "overview" | "events" | "alerts" | "analyzers" | "snapshots" | "reports" | "demo";

const navItems: Array<{ id: ViewId; label: string }> = [
  { id: "overview", label: "总览" },
  { id: "events", label: "事件" },
  { id: "alerts", label: "告警" },
  { id: "analyzers", label: "分析器" },
  { id: "snapshots", label: "快照/恢复" },
  { id: "reports", label: "报告" },
  { id: "demo", label: "Demo/关于" },
];

export default function App() {
  const [activeView, setActiveView] = useState<ViewId>("overview");
  const {
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
  } = useFileGuardData();

  const renderView = () => {
    if (loading) return <SkeletonRows rows={8} />;
    if (activeView === "overview") return <OverviewView data={data} onOpenAlerts={() => setActiveView("alerts")} />;
    if (activeView === "events") return <EventsView events={data.events} />;
    if (activeView === "alerts") return <AlertsView alerts={data.alerts} />;
    if (activeView === "analyzers") return <AnalyzersView analyzers={data.analyzers} />;
    if (activeView === "snapshots") return <SnapshotsView snapshots={data.snapshots} />;
    if (activeView === "reports") return <ReportsView reports={data.reports} onGenerate={generateReport} />;
    return <DemoView data={data} dataMode={dataMode} connectionMode={connectionMode} onUseDemo={useDemoData} />;
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <strong>FileGuard</strong>
          <span>Web Console</span>
        </div>
        <nav>
          {navItems.map((item) => (
            <button
              className={activeView === item.id ? "active" : ""}
              key={item.id}
              onClick={() => setActiveView(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <h1>文件安全风险感知控制台</h1>
            <p>感知、分析、响应与展示闭环</p>
          </div>
          <div className="topbar-status">
            <StatusBadge ok={data.status.running}>{data.status.running ? "Monitor 运行" : "Monitor 停止"}</StatusBadge>
            <StatusBadge ok={dataMode === "api"}>{dataMode === "api" ? "真实 API" : "Demo data mode"}</StatusBadge>
            <StatusBadge ok={connectionMode === "realtime"}>{connectionMode === "realtime" ? "SSE 实时" : connectionMode === "polling" ? "轮询" : "离线"}</StatusBadge>
            <LevelBadge level={data.status.highest_level} />
          </div>
        </header>

        {dataMode === "demo" ? <div className="demo-banner">Demo data mode：当前展示为演示数据，不代表真实监控结果。</div> : null}
        <ErrorBanner message={error} />

        <div className="control-row">
          <button className="primary-button" onClick={() => void refresh()}>手动刷新</button>
          <label className="switch-row">
            <input type="checkbox" checked={autoRefresh} onChange={(event) => setAutoRefresh(event.target.checked)} />
            自动刷新
          </label>
          <span className="muted-text">最近更新：{formatTime(lastUpdated)}</span>
        </div>

        {renderView()}
      </main>
    </div>
  );
}
