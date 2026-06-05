import { useState, type ReactNode } from "react";
import { CheckCircle2, FileCode, FileText, Info } from "lucide-react";
import { Chip, ContentCard, CopyButton, FieldLabel, PrimaryButton } from "../atoms";
import { formatTime } from "../data";
import type { ReportStatusResponse } from "../data";

export function Reports({
  reports,
  onGenerate,
}: {
  reports: ReportStatusResponse;
  onGenerate: () => Promise<ReportStatusResponse>;
}) {
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<{ kind: "ok" | "err"; msg: string } | null>(null);

  async function generate() {
    setLoading(true);
    try {
      const result = await onGenerate();
      setToast({ kind: result.ok ? "ok" : "err", msg: result.ok ? `报告已生成：${result.report_file}` : result.error ?? "报告生成失败" });
    } catch (caught) {
      setToast({ kind: "err", msg: caught instanceof Error ? caught.message : "报告生成失败" });
    } finally {
      setLoading(false);
      window.setTimeout(() => setToast(null), 3200);
    }
  }

  const reportName = reports.generated_at ? `report_${reports.generated_at.slice(0, 10)}.html` : "report.html";

  return (
    <div className="space-y-4">
      <ContentCard
        title="HTML Report Artifact"
        subtitle={<span className="fg-mono">/api/reports</span>}
        extra={<PrimaryButton onClick={() => void generate()} loading={loading} icon={<FileText size={13} />}>{loading ? "生成中…" : "生成报告"}</PrimaryButton>}
      >
        <div style={{ border: "1px solid var(--fg-border)", borderRadius: 10, overflow: "hidden", background: "linear-gradient(180deg, #FAFCFE 0%, #FFFFFF 100%)" }}>
          <div className="flex items-center gap-2 px-4" style={{ height: 36, background: "#F1F5F9", borderBottom: "1px solid var(--fg-border)" }}>
            <span style={{ width: 9, height: 9, borderRadius: "50%", background: "#FCA5A5" }} />
            <span style={{ width: 9, height: 9, borderRadius: "50%", background: "#FDE68A" }} />
            <span style={{ width: 9, height: 9, borderRadius: "50%", background: "#86EFAC" }} />
            <span className="fg-mono flex items-center gap-1.5" style={{ marginLeft: 12, fontSize: 11.5, color: "var(--fg-text-2)" }}>
              <FileCode size={12} />
              {reportName}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-5">
            <Cell label="available">
              {reports.available ? (
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 size={14} style={{ color: "var(--fg-success)" }} />
                  <span style={{ fontSize: 13.5, color: "var(--fg-text)", fontWeight: 600 }}>可用</span>
                </span>
              ) : (
                <span style={{ color: "var(--fg-text-2)" }}>未生成</span>
              )}
            </Cell>
            <Cell label="状态">
              <Chip mono color={reports.ok ? "#15803D" : "#9A3412"} bg={reports.ok ? "#DCFCE7" : "#FEE2E2"} border={reports.ok ? "#BBF7D0" : "#FCA5A5"}>
                {reports.ok ? "ok" : "error"}
              </Chip>
            </Cell>
            <Cell label="generated_at">
              <span className="fg-mono fg-num" style={{ fontSize: 12.5 }}>{formatTime(reports.generated_at)}</span>
            </Cell>
            <Cell label="events / alerts">
              <span className="fg-num" style={{ fontSize: 13.5, fontWeight: 600 }}>
                {reports.events_total.toLocaleString()}
                <span style={{ color: "var(--fg-text-3)", margin: "0 6px" }}>/</span>
                {reports.alerts_total.toLocaleString()}
              </span>
            </Cell>
          </div>

          <div className="px-5 pb-5">
            <FieldLabel>report_file</FieldLabel>
            <div className="flex items-center gap-2" style={{ padding: "10px 12px", background: "var(--fg-code-bg)", color: "var(--fg-code-text)", borderRadius: 6 }}>
              <span className="fg-mono flex-1" style={{ fontSize: 12, wordBreak: "break-all" }}>{reports.report_file}</span>
              <CopyButton text={reports.report_file} />
            </div>
          </div>
        </div>
      </ContentCard>

      <div
        className="flex gap-3"
        style={{
          padding: "14px 16px",
          background: "linear-gradient(180deg, #EFF6FF 0%, #F6FAFF 100%)",
          border: "1px solid #C7DCFB",
          borderRadius: 10,
          color: "#1E3A8A",
        }}
      >
        <span style={{ width: 24, height: 24, borderRadius: 6, background: "#DBEAFE", color: "#1D4ED8", display: "inline-flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <Info size={14} />
        </span>
        <div style={{ fontSize: 12.5, lineHeight: "20px", color: "#1E40AF" }}>
          <div style={{ fontWeight: 600, color: "#1E3A8A", marginBottom: 4 }}>报告打开说明</div>
          报告由后端写入本地 HTML 文件路径。若后端未暴露静态文件服务，需要在项目目录中手动打开{" "}
          <span className="fg-code-inline">report_file</span> 对应文件。
        </div>
      </div>

      {toast && (
        <div
          role="status"
          style={{
            position: "fixed",
            top: 24,
            left: "50%",
            transform: "translateX(-50%)",
            background: toast.kind === "ok" ? "#0F172A" : "#7F1D1D",
            color: "white",
            padding: "10px 14px",
            borderRadius: 8,
            fontSize: 13,
            boxShadow: "var(--fg-shadow-float)",
            zIndex: 60,
            animation: "fg-fade-up 180ms ease-out",
          }}
        >
          <span style={{ opacity: 0.7, marginRight: 8 }}>{toast.kind === "ok" ? "✓" : "!"}</span>
          {toast.msg}
        </div>
      )}
    </div>
  );
}

function Cell({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <FieldLabel>{label}</FieldLabel>
      <div>{children}</div>
    </div>
  );
}
