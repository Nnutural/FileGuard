import { useMemo, useState } from "react";
import { Card, Drawer, EmptyState, LevelBadge, PathText, formatBytes, formatTime, relativeTime } from "../components/common";
import type { EventItem, EventsResponse } from "../types";

type SortKey = "timestamp" | "event_type" | "signals_count";

export function EventsView({ events }: { events: EventsResponse }) {
  const [eventType, setEventType] = useState("all");
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("timestamp");
  const [selected, setSelected] = useState<EventItem | null>(null);

  const types = useMemo(() => Array.from(new Set(events.events.map((event) => event.event_type))).sort(), [events.events]);
  const filtered = useMemo(() => {
    const rows = events.events.filter((event) => {
      const matchesType = eventType === "all" || event.event_type === eventType;
      const path = `${event.src_path} ${event.dest_path ?? ""}`.toLowerCase();
      return matchesType && path.includes(query.toLowerCase());
    });
    return rows.sort((a, b) => {
      if (sortKey === "timestamp") return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      if (sortKey === "signals_count") return b.signals_count - a.signals_count;
      return a.event_type.localeCompare(b.event_type);
    });
  }, [eventType, events.events, query, sortKey]);

  return (
    <Card title="文件事件">
      <div className="toolbar">
        <select value={eventType} onChange={(event) => setEventType(event.target.value)}>
          <option value="all">全部类型</option>
          {types.map((type) => <option value={type} key={type}>{type}</option>)}
        </select>
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索路径" />
        <select value={sortKey} onChange={(event) => setSortKey(event.target.value as SortKey)}>
          <option value="timestamp">按时间</option>
          <option value="event_type">按类型</option>
          <option value="signals_count">按信号数</option>
        </select>
      </div>
      {filtered.length === 0 ? <EmptyState text="没有匹配的事件" /> : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>类型</th>
                <th>路径</th>
                <th>目标</th>
                <th>大小</th>
                <th>风险</th>
                <th>信号</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 100).map((event) => (
                <tr key={`${event.timestamp}-${event.src_path}`} onClick={() => setSelected(event)}>
                  <td title={formatTime(event.timestamp)}>{relativeTime(event.timestamp)}</td>
                  <td>{event.event_type}</td>
                  <td><PathText path={event.src_path} /></td>
                  <td><PathText path={event.dest_path} /></td>
                  <td>{formatBytes(event.file_size)}</td>
                  <td><LevelBadge level={event.level} /></td>
                  <td>{event.signals_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Drawer title="事件详情" open={selected !== null} onClose={() => setSelected(null)}>
        {selected ? <pre className="json-block">{JSON.stringify(selected, null, 2)}</pre> : null}
      </Drawer>
    </Card>
  );
}
