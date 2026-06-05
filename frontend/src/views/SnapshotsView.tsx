import { Card, EmptyState, PathText, StatusBadge, formatTime } from "../components/common";
import type { SnapshotsResponse } from "../types";

function shortHash(value: string | null): string {
  return value ? value.slice(0, 12) : "-";
}

export function SnapshotsView({ snapshots }: { snapshots: SnapshotsResponse }) {
  return (
    <div className="view-stack">
      <div className="stat-grid">
        <div className="stat-card">
          <span>快照状态</span>
          <strong><StatusBadge ok={snapshots.enabled}>{snapshots.enabled ? "启用" : "关闭"}</StatusBadge></strong>
        </div>
        <div className="stat-card">
          <span>Baseline 文件数</span>
          <strong>{snapshots.files_total}</strong>
        </div>
        <div className="stat-card">
          <span>增量记录</span>
          <strong>{snapshots.incremental_total}</strong>
        </div>
        <div className="stat-card">
          <span>恢复校验</span>
          <strong>{snapshots.last_restore_verified === null ? "-" : snapshots.last_restore_verified ? "PASS" : "FAIL"}</strong>
        </div>
      </div>
      <Card title="Baseline 与备份">
        <div className="key-value">
          <span>Baseline 文件</span><PathText path={snapshots.baseline_file} />
          <span>备份目录</span><PathText path={snapshots.backup_dir} />
          <span>最近快照</span><strong>{formatTime(snapshots.last_snapshot_time)}</strong>
        </div>
      </Card>
      <Card title="最近增量快照">
        {snapshots.incremental_records.length === 0 ? <EmptyState text="暂无运行期增量记录" /> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>时间</th>
                  <th>类型</th>
                  <th>路径</th>
                  <th>Hash 变化</th>
                  <th>熵值变化</th>
                </tr>
              </thead>
              <tbody>
                {snapshots.incremental_records.map((record) => (
                  <tr key={`${record.timestamp}-${record.path}`}>
                    <td>{formatTime(record.timestamp)}</td>
                    <td>{record.event_type}</td>
                    <td><PathText path={record.path} /></td>
                    <td>{shortHash(record.old_hash)} → {shortHash(record.new_hash)}</td>
                    <td>{record.old_entropy?.toFixed(2) ?? "-"} → {record.new_entropy?.toFixed(2) ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      <Card title="自动恢复动作">
        {snapshots.auto_restore_actions.length === 0 ? <EmptyState text="暂无自动恢复动作；默认关闭或尚未触发" /> : (
          <pre className="json-block">{JSON.stringify(snapshots.auto_restore_actions, null, 2)}</pre>
        )}
      </Card>
    </div>
  );
}
