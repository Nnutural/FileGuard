import { useMemo, useState, type ReactNode } from "react";
import {
  Chip,
  ContentCard,
  EmptyState,
  FieldLabel,
  JsonCodeBlock,
  PathCell,
  RiskBadge,
} from "../atoms";
import { formatBytes, formatScore, formatTime } from "../data";
import type { EventItem, EventsResponse } from "../data";
import { DetailDrawer } from "../Drawer";
import { Filter, Inbox, RefreshCw, Search } from "lucide-react";

const EVENT_TYPE_COLORS: Record<string, { c: string; bg: string; b: string }> = {
  created: { c: "#15803D", bg: "#F0FDF4", b: "#BBF7D0" },
  modified: { c: "#1E3A8A", bg: "#EAF1FF", b: "#C7D8FF" },
  deleted: { c: "#991B1B", bg: "#FEE2E2", b: "#FCA5A5" },
  renamed: { c: "#7C3AED", bg: "#F5F3FF", b: "#DDD6FE" },
  moved: { c: "#854D0E", bg: "#FEF9C3", b: "#FDE68A" },
};

type SortKey = "time_desc" | "risk_desc" | "size_desc" | "signals_desc";

export function Events({ events, onRefresh }: { events: EventsResponse; onRefresh: () => Promise<void> }) {
  const [type, setType] = useState("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("time_desc");
  const [open, setOpen] = useState<EventItem | null>(null);
  const [loading, setLoading] = useState(false);

  const types = useMemo(() => Array.from(new Set(events.events.map((event) => event.event_type))).sort(), [events.events]);
  const filtered = useMemo(() => {
    const rows = events.events.filter((event) => {
      const matchesType = type === "all" || event.event_type === type;
      const pathText = `${event.src_path} ${event.dest_path ?? ""}`.toLowerCase();
      return matchesType && pathText.includes(query.toLowerCase());
    });
    return rows.slice().sort((a, b) => {
      if (sort === "time_desc") return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      if (sort === "risk_desc") return (b.score ?? -1) - (a.score ?? -1);
      if (sort === "size_desc") return (b.file_size ?? -1) - (a.file_size ?? -1);
      return b.signals_count - a.signals_count;
    });
  }, [events.events, query, sort, type]);

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
          value={type}
          onChange={setType}
          options={[{ v: "all", l: "全部类型" }, ...types.map((item) => ({ v: item, l: item }))]}
        />
        <SearchInput value={query} onChange={setQuery} placeholder="搜索路径，例如 plan.docx" />
        <SelectInput
          value={sort}
          onChange={(value) => setSort(value as SortKey)}
          options={[
            { v: "time_desc", l: "时间降序" },
            { v: "risk_desc", l: "风险降序" },
            { v: "size_desc", l: "文件大小降序" },
            { v: "signals_desc", l: "信号数降序" },
          ]}
        />
        <button className="fg-btn fg-btn-secondary" onClick={() => void refresh()} disabled={loading}>
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
          刷新
        </button>
      </FilterToolbar>

      <ContentCard
        title="事件流"
        subtitle={<span className="fg-mono">{filtered.length.toString().padStart(2, "0")} / {events.total} entries</span>}
        padding={false}
      >
        {filtered.length === 0 ? (
          <EmptyState title="未匹配到事件" desc="尝试调整事件类型、清空搜索关键字，或切换排序条件。" icon={<Inbox size={20} />} />
        ) : (
          <div className="overflow-x-auto">
            <table className="fg-table">
              <thead>
                <tr>
                  <Th>时间</Th>
                  <Th>类型</Th>
                  <Th>路径</Th>
                  <Th>目标</Th>
                  <Th>大小</Th>
                  <Th>风险</Th>
                  <Th>信号</Th>
                </tr>
              </thead>
              <tbody>
                {filtered.slice(0, 200).map((event) => {
                  const tag = EVENT_TYPE_COLORS[event.event_type] ?? EVENT_TYPE_COLORS.modified;
                  const selected = open === event;
                  return (
                    <tr key={`${event.timestamp}-${event.src_path}-${event.dest_path ?? ""}`} data-selected={selected} onClick={() => setOpen(event)}>
                      <td>
                        <span className="fg-mono fg-num" style={{ color: "var(--fg-text-2)", fontSize: 11.5 }}>
                          {formatTime(event.timestamp)}
                        </span>
                      </td>
                      <td><Chip color={tag.c} bg={tag.bg} border={tag.b} mono>{event.event_type}</Chip></td>
                      <td><PathCell path={event.src_path} max={44} /></td>
                      <td><PathCell path={event.dest_path} max={32} /></td>
                      <td><span className="fg-mono fg-num" style={{ fontSize: 12 }}>{formatBytes(event.file_size)}</span></td>
                      <td><RiskBadge level={event.level} /></td>
                      <td>
                        <span
                          className="fg-num"
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                            minWidth: 22,
                            height: 20,
                            padding: "0 6px",
                            borderRadius: 10,
                            background: "var(--fg-primary-soft)",
                            color: "var(--fg-primary)",
                            fontSize: 11,
                            fontWeight: 600,
                            border: "1px solid #D6E2FB",
                          }}
                        >
                          {event.signals_count}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </ContentCard>

      <DetailDrawer open={!!open} onClose={() => setOpen(null)} title="事件详情" subtitle={open && <span>event · {formatTime(open.timestamp)}</span>}>
        {open && (
          <div className="space-y-5">
            <div className="flex items-center gap-2">
              <RiskBadge level={open.level} />
              <Chip color="#1E3A8A" bg="#EAF1FF" border="#C7D8FF" mono>{open.event_type}</Chip>
              <span className="fg-num" style={{ marginLeft: "auto", fontSize: 13, color: "var(--fg-text)", fontWeight: 600 }}>
                score {formatScore(open.score)}
              </span>
            </div>

            <Field label="src_path" value={open.src_path} mono />
            <Field label="dest_path" value={open.dest_path ?? "—"} mono />

            <div className="grid grid-cols-2 gap-4">
              <Field label="file_size" value={formatBytes(open.file_size)} />
              <Field label="is_directory" value={String(open.is_directory)} />
              <Field label="signals_count" value={String(open.signals_count)} />
              <Field label="level" value={open.level ?? "—"} />
            </div>

            <JsonCodeBlock data={open} label="原始 event payload" />
          </div>
        )}
      </DetailDrawer>
    </div>
  );
}

export function FilterToolbar({ children }: { children: ReactNode }) {
  return <div className="fg-card flex flex-wrap items-center gap-3" style={{ padding: 12 }}>{children}</div>;
}

export function SearchInput({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <div
      className="flex-1 min-w-[220px] flex items-center gap-2 px-3"
      style={{ height: 36, border: "1px solid var(--fg-border)", borderRadius: "var(--fg-radius-sm)", background: "white" }}
    >
      <Search size={13} style={{ color: "var(--fg-text-3)" }} />
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="flex-1 outline-none fg-mono"
        style={{ fontSize: 13, background: "transparent", color: "var(--fg-text)" }}
      />
      {value && (
        <button
          onClick={() => onChange("")}
          style={{ background: "transparent", border: 0, color: "var(--fg-text-3)", cursor: "pointer", fontSize: 12 }}
        >
          清除
        </button>
      )}
    </div>
  );
}

export function SelectInput({
  value,
  onChange,
  options,
  icon,
}: {
  value: string;
  onChange: (value: string) => void;
  options: { v: string; l: string }[];
  icon?: ReactNode;
}) {
  return (
    <label
      className="flex items-center gap-1.5 px-2 pl-3"
      style={{ height: 36, border: "1px solid var(--fg-border)", borderRadius: "var(--fg-radius-sm)", background: "white", color: "var(--fg-text-2)" }}
    >
      {icon}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="outline-none"
        style={{ background: "transparent", fontSize: 13, color: "var(--fg-text)", border: 0, paddingRight: 4, cursor: "pointer" }}
      >
        {options.map((option) => <option key={option.v} value={option.v}>{option.l}</option>)}
      </select>
    </label>
  );
}

export function Th({ children }: { children: ReactNode }) {
  return <th>{children}</th>;
}

export function Td({ children }: { children: ReactNode }) {
  return <td>{children}</td>;
}

export function Field({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <FieldLabel>{label}</FieldLabel>
      <div className={mono ? "fg-mono" : ""} style={{ color: "var(--fg-text)", fontSize: 13, wordBreak: "break-all", lineHeight: "20px" }}>
        {value}
      </div>
    </div>
  );
}
