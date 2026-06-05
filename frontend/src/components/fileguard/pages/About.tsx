import type { ReactNode } from "react";
import { CheckCircle2, Clock, Database, Info, Radio, Tag } from "lucide-react";
import { Chip, ContentCard, FieldLabel, SecondaryButton } from "../atoms";
import { formatTime } from "../data";
import type { ReportStatusResponse } from "../data";
import type { ConnectionMode, DataMode } from "../../../types";

export function About({
  dataMode,
  connectionMode,
  reports,
  onUseDemo,
  onTryApi,
}: {
  dataMode: DataMode;
  connectionMode: ConnectionMode;
  reports: ReportStatusResponse;
  onUseDemo: () => void;
  onTryApi: () => Promise<void>;
}) {
  const capabilities = [
    "本地文件事件展示",
    "风险评分展示",
    "分析器状态展示",
    "快照与恢复记录展示",
    "HTML 报告状态展示",
  ];
  const exclusions = [
    "前端不执行检测算法",
    "前端不读取本地文件",
    "无用户管理 / 登录",
    "无远程隔离 / 处置",
  ];

  return (
    <div className="space-y-4">
      <ContentCard title="当前会话" subtitle="session metadata">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <InfoCard
            icon={<Database size={14} />}
            label="当前模式"
            value={
              <Chip mono color={dataMode === "demo" ? "#854D0E" : "#15803D"} bg={dataMode === "demo" ? "#FEF9C3" : "#DCFCE7"} border={dataMode === "demo" ? "#FDE68A" : "#BBF7D0"}>
                {dataMode === "demo" ? "Demo data mode" : "真实 API"}
              </Chip>
            }
          />
          <InfoCard
            icon={<Radio size={14} />}
            label="连接状态"
            value={
              <Chip
                mono
                color={connectionMode === "realtime" ? "#15803D" : connectionMode === "polling" ? "#854D0E" : "#475569"}
                bg={connectionMode === "realtime" ? "#DCFCE7" : connectionMode === "polling" ? "#FEF9C3" : "#F1F5F9"}
                border={connectionMode === "realtime" ? "#BBF7D0" : connectionMode === "polling" ? "#FDE68A" : "#E2E8F0"}
              >
                {connectionMode === "realtime" ? "SSE 实时" : connectionMode === "polling" ? "轮询" : "离线"}
              </Chip>
            }
          />
          <InfoCard icon={<Tag size={14} />} label="版本" value={<span className="fg-mono" style={{ fontSize: 13 }}>FileGuard 0.1.0 · Web Console</span>} />
          <InfoCard icon={<Clock size={14} />} label="最近报告" value={<span className="fg-mono fg-num" style={{ fontSize: 13 }}>{formatTime(reports.generated_at)}</span>} />
        </div>
      </ContentCard>

      <ContentCard title="Demo data mode" subtitle="离线展示模式">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div className="flex gap-3" style={{ color: "var(--fg-text-2)", fontSize: 13, lineHeight: "20px", maxWidth: 640 }}>
            <Info size={18} style={{ flexShrink: 0, marginTop: 1, color: "var(--fg-primary)" }} />
            <span>
              <span style={{ color: "var(--fg-text)", fontWeight: 600 }}>Demo data mode 仅用于离线展示。</span>{" "}
              数据结构与后端 DTO（Status / EventItem / AlertItem / SignalItem / AnalyzerItem / SnapshotsResponse / ReportStatusResponse）完全一致，
              但不代表真实监控结果。真实 API 模式仍通过 SSE 优先、轮询回退的方式从后端拉取数据。
            </span>
          </div>
          <div style={{ flexShrink: 0 }}>
            <SecondaryButton onClick={() => { dataMode === "demo" ? void onTryApi() : onUseDemo(); }}>
              {dataMode === "demo" ? "尝试真实 API" : "切换到 Demo data mode"}
            </SecondaryButton>
          </div>
        </div>
      </ContentCard>

      <ContentCard title="关于 FileGuard" subtitle="capability boundary">
        <div style={{ color: "var(--fg-text-2)", fontSize: 13, lineHeight: "22px", marginBottom: 16 }}>
          FileGuard 是一个面向防御场景的本地文件安全风险感知与保护验证系统。Web Console 仅负责
          呈现后端 DTO 数据，前端不执行检测算法、不读取本地文件、不实现远程处置。
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <FieldLabel>能力边界</FieldLabel>
            <div className="space-y-1.5">
              {capabilities.map((capability) => (
                <div
                  key={capability}
                  className="flex items-center gap-2 px-3"
                  style={{ height: 36, background: "#FAFCFE", border: "1px solid var(--fg-border-soft)", borderRadius: 6 }}
                >
                  <CheckCircle2 size={14} style={{ color: "var(--fg-success)" }} />
                  <span style={{ fontSize: 13, color: "var(--fg-text)" }}>{capability}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <FieldLabel>明确不做</FieldLabel>
            <div className="space-y-1.5">
              {exclusions.map((item) => (
                <div
                  key={item}
                  className="flex items-center gap-2 px-3"
                  style={{ height: 36, background: "#FAFCFE", border: "1px solid var(--fg-border-soft)", borderRadius: 6 }}
                >
                  <span
                    style={{
                      width: 14,
                      height: 14,
                      borderRadius: "50%",
                      background: "#FEE2E2",
                      color: "#991B1B",
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 11,
                      fontWeight: 700,
                    }}
                  >
                    ×
                  </span>
                  <span style={{ fontSize: 13, color: "var(--fg-text)" }}>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </ContentCard>
    </div>
  );
}

function InfoCard({ icon, label, value }: { icon: ReactNode; label: string; value: ReactNode }) {
  return (
    <div style={{ border: "1px solid var(--fg-border-soft)", borderRadius: 8, padding: 14, background: "#FAFCFE" }}>
      <div className="flex items-center gap-2 mb-2" style={{ color: "var(--fg-text-2)" }}>
        <span
          style={{
            width: 22,
            height: 22,
            borderRadius: 5,
            background: "var(--fg-primary-soft)",
            color: "var(--fg-primary)",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            border: "1px solid #D6E2FB",
          }}
        >
          {icon}
        </span>
        <FieldLabel>{label}</FieldLabel>
      </div>
      <div>{value}</div>
    </div>
  );
}
