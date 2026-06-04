import { useEffect, useState } from "react";
import { api } from "../api/fileguard";
import type { Status } from "../types";

export function StatusPanel() {
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => {
    const tick = () => { api.getStatus().then(setStatus).catch(console.error); };
    tick();
    const id = setInterval(tick, 3000);
    return () => clearInterval(id);
  }, []);

  if (!status) return <div className="card"><h2>系统状态</h2><p>加载中...</p></div>;

  return (
    <div className="card">
      <h2>系统状态</h2>
      <p>运行: {status.running ? "是" : "否"}</p>
      <p>已处理事件: {status.events_processed}</p>
      <p>队列长度: {status.queue_size}</p>
      <p>运行时间: {Math.round(status.uptime_seconds)}s</p>
    </div>
  );
}
