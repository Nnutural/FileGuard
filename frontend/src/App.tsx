import { useState } from "react";
import { AlertCircle, ChevronRight, Info } from "lucide-react";
import { MobileNav, NAV_ITEMS, PageKey, Sidebar } from "./components/fileguard/Sidebar";
import { TopBar } from "./components/fileguard/TopBar";
import { Overview } from "./components/fileguard/pages/Overview";
import { Events } from "./components/fileguard/pages/Events";
import { Alerts } from "./components/fileguard/pages/Alerts";
import { Analyzers } from "./components/fileguard/pages/Analyzers";
import { Snapshots } from "./components/fileguard/pages/Snapshots";
import { Reports } from "./components/fileguard/pages/Reports";
import { About } from "./components/fileguard/pages/About";
import { useFileGuardData } from "./hooks/useFileGuardData";

export default function App() {
  const [page, setPage] = useState<PageKey>("overview");
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
  const current = NAV_ITEMS.find((item) => item.key === page);

  return (
    <div className="fg-app-bg h-full w-full" style={{ color: "var(--fg-text)" }}>
      <div className="flex h-full w-full" style={{ padding: 12, gap: 16 }}>
        <Sidebar current={page} onChange={setPage} />

        <div className="flex-1 flex flex-col min-w-0" style={{ gap: 12 }}>
          <TopBar
            status={data.status}
            dataMode={dataMode}
            connectionMode={connectionMode}
            autoRefresh={autoRefresh}
            lastUpdated={lastUpdated}
            onRefresh={refresh}
            onAutoRefreshChange={setAutoRefresh}
          />
          <MobileNav current={page} onChange={setPage} />

          {dataMode === "demo" && (
            <div className="fg-demo-banner">
              <span className="fg-banner-icon">
                <Info size={13} strokeWidth={2} />
              </span>
              <span className="flex-1">
                当前为 <b style={{ fontWeight: 600 }}>Demo data mode</b>, 数据仅用于离线展示, 结构与后端 DTO 一致,
                <span style={{ opacity: 0.85 }}> 不代表真实监控结果。</span>
              </span>
              <button
                onClick={() => setPage("about")}
                className="fg-btn fg-btn-ghost"
                style={{ color: "#7C4E0C", fontSize: 12, background: "transparent" }}
              >
                了解 Demo 模式
                <span className="fg-arrow" style={{ display: "inline-flex" }}>
                  <ChevronRight size={12} />
                </span>
              </button>
            </div>
          )}

          {error && (
            <div
              className="flex items-start gap-2"
              style={{
                padding: "10px 14px",
                background: "#FFF7ED",
                border: "1px solid #FED7AA",
                borderRadius: 10,
                color: "#7C2D12",
                fontSize: 12.5,
              }}
            >
              <AlertCircle size={15} style={{ marginTop: 1, flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          <main key={page} className="fg-page-enter flex-1 overflow-y-auto">
            <div className="flex items-baseline gap-2 mb-4 px-1">
              <h2 style={{ color: "var(--fg-text)", fontSize: 15, fontWeight: 600 }}>{current?.label}</h2>
              <span className="fg-mono" style={{ color: "var(--fg-text-3)", fontSize: 11, letterSpacing: "0.06em" }}>
                / fileguard / {current?.key}
              </span>
            </div>

            {loading ? (
              <LoadingState />
            ) : (
              <>
                {page === "overview" && <Overview data={data} onGoto={setPage} />}
                {page === "events" && <Events events={data.events} onRefresh={refresh} />}
                {page === "alerts" && <Alerts alerts={data.alerts} onRefresh={refresh} />}
                {page === "analyzers" && <Analyzers analyzers={data.analyzers} />}
                {page === "snapshots" && <Snapshots snapshots={data.snapshots} />}
                {page === "reports" && <Reports reports={data.reports} onGenerate={generateReport} />}
                {page === "about" && (
                  <About
                    dataMode={dataMode}
                    connectionMode={connectionMode}
                    reports={data.reports}
                    onUseDemo={useDemoData}
                    onTryApi={refresh}
                  />
                )}
              </>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          key={index}
          className="fg-card"
          style={{
            height: index < 2 ? 88 : 132,
            background: "linear-gradient(90deg, #F1F5F9, #FFFFFF, #F1F5F9)",
            backgroundSize: "200% 100%",
            animation: "loading 1.2s infinite",
          }}
        />
      ))}
    </div>
  );
}
