import { useMemo, useState } from "react";
import {
  Chip,
  ContentCard,
  EmptyState,
  FieldLabel,
  JsonCodeBlock,
  PathCell,
  RiskBadge,
  ScoreMeter,
} from "../atoms";
import { compareRiskLevels, formatScore, formatTime } from "../data";
import type { AlertItem, RiskLevel } from "../data";
import type { AlertsResponse } from "../../../types";
import { DetailDrawer } from "../Drawer";
import { Filter, RefreshCw, ShieldX } from "lucide-react";
import { Field, FilterToolbar, SearchInput, SelectInput, Td, Th } from "./Events";

type SortKey = "time_desc" | "score_desc" | "level_desc";

export function Alerts({ alerts, onRefresh }: { alerts: AlertsResponse; onRefresh: () => Promise<void> }) {
  const [level, setLevel] = useState<RiskLevel | "all">("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("time_desc");
  const [open, setOpen] = useState<AlertItem | null>(null);
  const [loading, setLoading] = useState(false);

  const filtered = useMemo(() => {
    const rows = alerts.alerts.filter((alert) => {
      const matchesLevel = level === "all" || alert.level === level;
      const pathText = `${alert.src_path} ${alert.dest_path ?? ""}`.toLowerCase();
      return matchesLevel && pathText.includes(query.toLowerCase());
    });
    return rows.slice().sort((a, b) => {
      if (sort === "time_desc") return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      if (sort === "score_desc") return b.score - a.score;
      return compareRiskLevels(b.level, a.level);
    });
  }, [alerts.alerts, level, query, sort]);

  async function refresh() {
    setLoading(true);
    try {
      await onRefresh();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <FilterToolbar>
        <SelectInput
          icon={<Filter size={12} />}
          value={level}
          onChange={(value) => setLevel(value as RiskLevel | "all")}
          options={[
            { v: "all", l: "全部等级" },
            { v: "LOW", l: `LOW (${alerts.by_level.LOW})` },
            { v: "MEDIUM", l: `MEDIUM (${alerts.by_level.MEDIUM})` },
            { v: "HIGH", l: `HIGH (${alerts.by_level.HIGH})` },
            { v: "CRITICAL", l: `CRITICAL (${alerts.by_level.CRITICAL})` },
          ]}
        />
        <SearchInput value={query} onChange={setQuery} placeholder="搜索路径..." />
        <SelectInput
          value={sort}
          onChange={(value) => setSort(value as SortKey)}
          options={[
            { v: "time_desc", l: "时间降序" },
            { v: "score_desc", l: "分数降序" },
            { v: "level_desc", l: "等级优先" },
          ]}
        />
        <button className="fg-btn fg-btn-secondary" onClick={() => void refresh()} disabled={loading}>
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
          刷新
        </button>
      </FilterToolbar>

      <ContentCard
        title="告警列表"
        subtitle={<span className="fg-mono">{filtered.length} alerts · 已升级 {filtered.filter((alert) => alert.escalated).length}</span>}
        padding={false}
      >
        {filtered.length === 0 ? (
          <EmptyState title="暂无告警" desc="当前筛选条件下没有匹配的告警记录。系统正在持续监听本地文件事件。" icon={<ShieldX size={20} />} />
        ) : (
          <div className="overflow-x-auto">
            <table className="fg-table">
              <thead>
                <tr>
                  <Th>等级</Th>
                  <Th>分数</Th>
                  <Th>路径</Th>
                  <Th>信号</Th>
                  <Th>升级</Th>
                  <Th>时间</Th>
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 200).map((alert) => (
                  <tr key={`${alert.timestamp}-${alert.src_path}`} data-selected={open === alert} onClick={() => setOpen(alert)}>
                    <Td><RiskBadge level={alert.level} /></Td>
                    <Td><ScoreMeter score={alert.score} /></Td>
                    <Td><PathCell path={alert.src_path} max={42} /></Td>
                    <Td>
                      <div className="flex gap-1 flex-wrap">
                        {alert.signal_types.slice(0, 2).map((signal) => (
                          <Chip key={signal} color="#1E3A8A" bg="#EAF1FF" border="#C7D8FF" mono>{signal}</Chip>
                        ))}
                        {alert.signal_types.length > 2 && <Chip mono>+{alert.signal_types.length - 2}</Chip>}
                      </div>
                    </Td>
                    <Td>
                      {alert.escalated ? (
                        <Chip color="#9A3412" bg="#FFEDD5" border="#FED7AA" mono>↑ 已升级</Chip>
                      ) : (
                        <span style={{ color: "var(--fg-text-3)", fontSize: 12 }}>—</span>
                      )}
                    </Td>
                    <Td><span className="fg-mono fg-num" style={{ color: "var(--fg-text-2)", fontSize: 11.5 }}>{formatTime(alert.timestamp)}</span></Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ContentCard>

      <DetailDrawer open={!!open} onClose={() => setOpen(null)} title="告警详情" subtitle={open && <span>alert · {formatTime(open.timestamp)}</span>}>
        {open && <AlertDetailBody alert={open} />}
      </DetailDrawer>
    </div>
  );
}

export function AlertDetailBody({ alert }: { alert: AlertItem }) {
  return (
    <div className="space-y-5">
      <div
        style={{
          padding: 14,
          borderRadius: 8,
          border: "1px solid var(--fg-border)",
          background: "linear-gradient(180deg, #FAFCFE 0%, #FFFFFF 100%)",
        }}
      >
        <div className="flex items-center gap-2 mb-2">
          <RiskBadge level={alert.level} />
          <Chip color="#1E3A8A" bg="#EAF1FF" border="#C7D8FF" mono>{alert.event_type}</Chip>
          {alert.escalated && <Chip color="#9A3412" bg="#FFEDD5" border="#FED7AA" mono>↑ escalated</Chip>}
          <span className="fg-num" style={{ marginLeft: "auto", fontSize: 22, fontWeight: 700, color: "var(--fg-text)" }}>
            {formatScore(alert.score)}
          </span>
        </div>
        <ScoreMeter score={alert.score} />
        <div className="fg-mono mt-2" style={{ fontSize: 11, color: "var(--fg-text-3)" }}>{formatTime(alert.timestamp)}</div>
      </div>

      <Field label="src_path" value={alert.src_path} mono />
      <Field label="dest_path" value={alert.dest_path ?? "—"} mono />

      <div>
        <FieldLabel>analyzers</FieldLabel>
        <div className="flex gap-1.5 flex-wrap">
          {alert.analyzers.map((analyzer) => <Chip key={analyzer} color="#003399" bg="#EAF1FF" border="#C7D8FF" mono>{analyzer}</Chip>)}
        </div>
      </div>

      {alert.escalation_reason && (
        <div
          style={{
            padding: 12,
            borderRadius: 8,
            border: "1px solid #FED7AA",
            background: "#FFF7ED",
            color: "#7C2D12",
            fontSize: 12.5,
            lineHeight: "20px",
          }}
        >
          <div className="fg-mono mb-1" style={{ fontSize: 10.5, letterSpacing: "0.08em", textTransform: "uppercase", color: "#9A3412" }}>
            escalation reason
          </div>
          {alert.escalation_reason}
        </div>
      )}

      <div>
        <FieldLabel>signals · {alert.signals.length}</FieldLabel>
        <div className="space-y-2.5">
          {alert.signals.map((signal) => (
            <div key={`${signal.timestamp}-${signal.analyzer_name}-${signal.signal_type}`} style={{ border: "1px solid var(--fg-border)", borderRadius: 8, background: "white", overflow: "hidden" }}>
              <div className="flex items-center gap-2 px-3 py-2" style={{ background: "#F8FAFC", borderBottom: "1px solid var(--fg-border-soft)" }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--fg-primary)" }} />
                <span style={{ fontSize: 12.5, color: "var(--fg-text)", fontWeight: 600 }}>{signal.analyzer_name}</span>
                <Chip color="#1E3A8A" bg="#EAF1FF" border="#C7D8FF" mono>{signal.signal_type}</Chip>
                <span className="fg-mono fg-num" style={{ marginLeft: "auto", fontSize: 11, color: "var(--fg-text-2)" }}>
                  w {signal.weight.toFixed(2)} · v {signal.value.toFixed(2)}
                </span>
              </div>
              <div className="px-3 py-2.5">
                <JsonCodeBlock data={signal.evidence} label="evidence" />
              </div>
            </div>
          ))}
        </div>
      </div>

      <JsonCodeBlock data={alert} label="完整 AlertItem" />
    </div>
  );
}
