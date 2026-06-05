import { useState } from "react";
import { Card, EmptyState, PathText, StatusBadge, formatTime } from "../components/common";
import type { ReportStatusResponse } from "../types";

export function ReportsView({
  reports,
  onGenerate,
}: {
  reports: ReportStatusResponse;
  onGenerate: () => Promise<ReportStatusResponse>;
}) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleGenerate() {
    setBusy(true);
    setMessage(null);
    try {
      const result = await onGenerate();
      setMessage(result.ok ? `报告已生成：${result.report_file}` : result.error ?? "报告生成失败");
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "报告生成失败");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="view-stack">
      <Card title="报告状态" actions={<button className="primary-button" disabled={busy} onClick={handleGenerate}>{busy ? "生成中..." : "生成报告"}</button>}>
        <div className="key-value">
          <span>可用状态</span><StatusBadge ok={reports.available}>{reports.available ? "已生成" : "未生成"}</StatusBadge>
          <span>报告路径</span><PathText path={reports.report_file} />
          <span>生成时间</span><strong>{formatTime(reports.generated_at)}</strong>
          <span>事件 / 告警</span><strong>{reports.events_total} / {reports.alerts_total}</strong>
        </div>
        {message ? <p className="notice">{message}</p> : null}
      </Card>
      <Card title="打开提示">
        {reports.available ? (
          <p>报告文件已写入本地路径。若后端未暴露静态文件，请在项目目录中打开该 HTML 文件。</p>
        ) : (
          <EmptyState text="还没有生成报告，点击右上角按钮触发 POST /api/reports。" />
        )}
      </Card>
    </div>
  );
}
