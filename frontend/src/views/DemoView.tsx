import { Card, StatusBadge, formatTime } from "../components/common";
import type { ConnectionMode, DashboardData, DataMode } from "../types";

export function DemoView({
  data,
  dataMode,
  connectionMode,
  onUseDemo,
}: {
  data: DashboardData;
  dataMode: DataMode;
  connectionMode: ConnectionMode;
  onUseDemo: () => void;
}) {
  return (
    <div className="view-stack">
      <Card title="数据来源">
        <div className="key-value">
          <span>当前模式</span><StatusBadge ok={dataMode === "api"}>{dataMode === "api" ? "真实 API" : "Demo data mode"}</StatusBadge>
          <span>连接状态</span><strong>{connectionMode}</strong>
          <span>版本</span><strong>FileGuard 0.1.0 / Web Console Round 4</strong>
          <span>最近报告</span><strong>{formatTime(data.reports.generated_at)}</strong>
        </div>
        <button className="secondary-button" onClick={onUseDemo}>切换到 Demo data mode</button>
      </Card>
      <Card title="Demo 说明">
        <p className="paragraph">
          Demo data mode 只用于前端离线展示。页面顶部会显示醒目标记，数据结构与后端 DTO 保持一致，但不会伪装成真实监控结果。
        </p>
        <p className="paragraph">
          课堂演示推荐流程：启动后端 monitor 与 API，打开前端控制台，观察 SSE/轮询状态，运行安全 demo 脚本，再在报告页触发 HTML 报告生成。
        </p>
      </Card>
    </div>
  );
}
