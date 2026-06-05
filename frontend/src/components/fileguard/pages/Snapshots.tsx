import { useState, type ReactNode } from "react";
import { Archive, ArrowRight, ChevronDown, FileStack, History, Layers, ShieldCheck } from "lucide-react";
import { Chip, ContentCard, CopyButton, EmptyState, FieldLabel, JsonCodeBlock, PathCell, StatCard } from "../atoms";
import { formatTime, recordValue } from "../data";
import type { SnapshotsResponse } from "../data";
import { Th } from "./Events";

function shortHash(value: string | null): string {
  return value ? value.slice(0, 12) : "—";
}

function entropyDelta(oldValue: number | null, newValue: number | null): string {
  if (oldValue === null || newValue === null) return "—";
  const delta = newValue - oldValue;
  return `${oldValue.toFixed(2)} → ${newValue.toFixed(2)} (${delta >= 0 ? "+" : ""}${delta.toFixed(2)})`;
}

export function Snapshots({ snapshots }: { snapshots: SnapshotsResponse }) {
  const [openIdx, setOpenIdx] = useState<number | null>(null);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="快照状态" value={snapshots.enabled ? "已启用" : "未启用"} sub={<span className="fg-mono">enabled</span>} icon={<Archive size={13} />} />
        <StatCard label="Baseline 文件数" value={snapshots.files_total.toLocaleString()} sub={<span className="fg-mono">files_total</span>} icon={<FileStack size={13} />} />
        <StatCard label="增量记录" value={snapshots.incremental_total} sub={<span className="fg-mono">incremental_total</span>} icon={<Layers size={13} />} />
        <StatCard
          label="恢复校验"
          value={snapshots.last_restore_verified === null ? "—" : snapshots.last_restore_verified ? "通过" : "未通过"}
          sub={<span className="fg-mono">last_restore_verified</span>}
          icon={<ShieldCheck size={13} />}
        />
      </div>

      <ContentCard title="Baseline 与备份链路" subtitle="baseline → backup → incremental">
        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr] gap-3 items-center">
          <PathPanel
            label="baseline_file"
            icon={<Archive size={14} />}
            path={snapshots.baseline_file}
            footer={<>last_snapshot · <span className="fg-num">{formatTime(snapshots.last_snapshot_time)}</span></>}
          />
          <div className="hidden md:flex flex-col items-center" style={{ color: "var(--fg-primary)" }}>
            <ArrowRight size={18} />
            <span className="fg-mono" style={{ fontSize: 10.5, color: "var(--fg-text-3)", marginTop: 2 }}>backup</span>
          </div>
          <PathPanel
            label="backup_dir"
            icon={<FileStack size={14} />}
            path={snapshots.backup_dir}
            footer={
              <>
                verified ·{" "}
                <span style={{ color: snapshots.last_restore_verified ? "var(--fg-success)" : "var(--fg-critical)" }}>
                  {snapshots.last_restore_verified === null ? "unknown" : snapshots.last_restore_verified ? "ok" : "fail"}
                </span>
              </>
            }
          />
        </div>
      </ContentCard>

      <ContentCard title="最近增量快照" subtitle={<span className="fg-mono">incremental records · {snapshots.incremental_records.length}</span>} padding={false}>
        {snapshots.incremental_records.length === 0 ? (
          <EmptyState title="暂无增量快照记录" desc="系统尚未捕获到 baseline 之后的文件变更。" icon={<History size={20} />} />
        ) : (
          <div className="overflow-x-auto">
            <table className="fg-table">
              <thead>
                <tr>
                  <Th>时间</Th>
                  <Th>类型</Th>
                  <Th>路径</Th>
                  <Th>Hash 变化</Th>
                  <Th>熵值变化</Th>
                </tr>
              </thead>
              <tbody>
                {snapshots.incremental_records.map((record) => {
                  const strong = record.old_entropy !== null && record.new_entropy !== null && record.new_entropy - record.old_entropy > 1;
                  return (
                    <tr key={`${record.timestamp}-${record.path}`} style={{ cursor: "default" }}>
                      <td><span className="fg-mono fg-num" style={{ color: "var(--fg-text-2)", fontSize: 11.5 }}>{formatTime(record.timestamp)}</span></td>
                      <td><Chip mono>{record.event_type}</Chip></td>
                      <td><PathCell path={record.path} max={44} /></td>
                      <td>
                        <span className="fg-mono" style={{ fontSize: 11.5, color: "var(--fg-text-2)" }}>
                          <span style={{ color: "var(--fg-text-3)" }}>{shortHash(record.old_hash)}</span>
                          <span style={{ margin: "0 6px", color: "var(--fg-primary)" }}>→</span>
                          <span style={{ color: "var(--fg-text)" }}>{shortHash(record.new_hash)}</span>
                        </span>
                      </td>
                      <td>
                        <Chip mono color={strong ? "#9A3412" : "var(--fg-text-2)"} bg={strong ? "#FFEDD5" : "#F1F5F9"} border={strong ? "#FED7AA" : "#E2E8F0"}>
                          {entropyDelta(record.old_entropy, record.new_entropy)}
                        </Chip>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </ContentCard>

      <ContentCard title="自动恢复动作" subtitle={<span className="fg-mono">auto_restore_actions</span>}>
        {snapshots.auto_restore_actions.length === 0 ? (
          <EmptyState title="暂无自动恢复动作" desc="系统尚未触发恢复流程。如果出现 CRITICAL 告警且 baseline 可用，会自动尝试从备份恢复。" icon={<ShieldCheck size={20} />} />
        ) : (
          <div className="space-y-1">
            {snapshots.auto_restore_actions.map((action, index) => {
              const last = index === snapshots.auto_restore_actions.length - 1;
              const result = recordValue(action, "result") ?? recordValue(action, "verified") ?? "recorded";
              const ok = result === "ok" || result === "true" || result === "verified";
              const label = recordValue(action, "action") ?? recordValue(action, "reason") ?? "auto_restore_action";
              const path = recordValue(action, "path") ?? "—";
              return (
                <div key={`${index}-${path}`} className="flex gap-3">
                  <div className="flex flex-col items-center" style={{ width: 14 }}>
                    <span
                      style={{
                        width: 10,
                        height: 10,
                        borderRadius: 5,
                        background: ok ? "var(--fg-success)" : "var(--fg-warn)",
                        marginTop: 6,
                        boxShadow: `0 0 0 3px ${ok ? "rgba(22,163,74,0.12)" : "rgba(180,83,9,0.12)"}`,
                      }}
                    />
                    {!last && <div style={{ width: 2, flex: 1, background: "var(--fg-border)", marginTop: 4 }} />}
                  </div>
                  <div className="flex-1 pb-4">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="fg-mono" style={{ fontSize: 13, color: "var(--fg-text)", fontWeight: 600 }}>{label}</span>
                      <Chip mono color={ok ? "#15803D" : "#9A3412"} bg={ok ? "#DCFCE7" : "#FEF3C7"} border={ok ? "#BBF7D0" : "#FDE68A"}>{result}</Chip>
                      <span className="fg-mono fg-num" style={{ color: "var(--fg-text-3)", fontSize: 11 }}>{recordValue(action, "timestamp") ?? "—"}</span>
                    </div>
                    <div className="fg-mono" style={{ fontSize: 11.5, color: "var(--fg-text-2)", marginBottom: 6 }}>{path}</div>
                    <button onClick={() => setOpenIdx(openIdx === index ? null : index)} className="fg-btn fg-btn-ghost" style={{ paddingLeft: 0 }}>
                      <ChevronDown size={12} style={{ transform: openIdx === index ? "rotate(180deg)" : "none", transition: "transform var(--fg-motion-fast)" }} />
                      {openIdx === index ? "收起 JSON" : "查看 JSON"}
                    </button>
                    {openIdx === index && <div className="mt-2"><JsonCodeBlock data={action} /></div>}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </ContentCard>
    </div>
  );
}

function PathPanel({
  label,
  icon,
  path,
  footer,
}: {
  label: string;
  icon: ReactNode;
  path: string | null;
  footer: ReactNode;
}) {
  const displayPath = path ?? "—";
  return (
    <div style={{ border: "1px solid var(--fg-border)", borderRadius: 8, background: "#FAFCFE", padding: 14 }}>
      <div className="flex items-center gap-2 mb-2" style={{ color: "var(--fg-primary)" }}>
        {icon}
        <FieldLabel>{label}</FieldLabel>
      </div>
      <div className="flex items-center gap-2">
        <span className="fg-mono flex-1" style={{ fontSize: 12.5, color: "var(--fg-text)", wordBreak: "break-all", lineHeight: "18px" }}>
          {displayPath}
        </span>
        {path && <CopyButton text={path} />}
      </div>
      <div className="fg-mono mt-2" style={{ fontSize: 11, color: "var(--fg-text-3)" }}>{footer}</div>
    </div>
  );
}
