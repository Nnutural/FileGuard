import {
  LayoutDashboard,
  ListOrdered,
  ShieldAlert,
  Activity,
  History,
  FileText,
  Info,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

export type PageKey =
  | "overview"
  | "events"
  | "alerts"
  | "analyzers"
  | "snapshots"
  | "reports"
  | "about";

type NavItem = { key: PageKey; label: string; icon: LucideIcon; section: string };

export const NAV_ITEMS: NavItem[] = [
  { key: "overview",  label: "总览",       icon: LayoutDashboard, section: "感知" },
  { key: "events",    label: "事件",       icon: ListOrdered,     section: "感知" },
  { key: "alerts",    label: "告警",       icon: ShieldAlert,     section: "分析" },
  { key: "analyzers", label: "分析器",     icon: Activity,        section: "分析" },
  { key: "snapshots", label: "快照 / 恢复",icon: History,         section: "响应" },
  { key: "reports",   label: "报告",       icon: FileText,        section: "展示" },
  { key: "about",     label: "Demo / 关于",icon: Info,            section: "展示" },
];

function groupItems(items: NavItem[]) {
  const out: { section: string; items: NavItem[] }[] = [];
  for (const it of items) {
    const last = out[out.length - 1];
    if (last && last.section === it.section) last.items.push(it);
    else out.push({ section: it.section, items: [it] });
  }
  return out;
}

export function Sidebar({
  current,
  onChange,
}: {
  current: PageKey;
  onChange: (p: PageKey) => void;
}) {
  const groups = groupItems(NAV_ITEMS);

  return (
    <aside
      className="fg-sidebar hidden md:flex flex-col"
      style={{ width: 248, flexShrink: 0 }}
    >
      {/* Brand */}
      <div
        className="px-4 pt-4 pb-3"
        style={{ borderBottom: "1px solid var(--fg-border-soft)" }}
      >
        <div className="flex items-center gap-2.5">
          <div className="fg-brand-mark">FG</div>
          <div className="flex-1 min-w-0">
            <div
              style={{
                color: "#0F172A",
                fontSize: 15,
                fontWeight: 700,
                letterSpacing: "0.005em",
                lineHeight: "18px",
              }}
            >
              FileGuard
            </div>
            <div
              className="fg-mono"
              style={{
                color: "#94A3B8",
                fontSize: 10,
                letterSpacing: "0.18em",
                textTransform: "uppercase",
                marginTop: 3,
              }}
            >
              Web Console
            </div>
          </div>
        </div>
        <div
          className="flex items-center gap-1.5 mt-3 px-2 py-1.5"
          style={{
            background: "#F4F8FF",
            border: "1px solid #D6E2FB",
            borderRadius: 6,
            color: "#1E3A8A",
            fontSize: 11,
          }}
        >
          <ShieldCheck size={12} style={{ color: "var(--fg-primary)" }} />
          <span>本地文件安全风险感知</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-1">
        {groups.map((g) => (
          <div key={g.section}>
            <div className="fg-sidebar-section">{g.section}</div>
            {g.items.map((item) => {
              const Active = current === item.key;
              const Icon = item.icon;
              return (
                <button
                  key={item.key}
                  onClick={() => onChange(item.key)}
                  data-active={Active}
                  className="fg-nav-item"
                >
                  <span className="fg-nav-icon">
                    <Icon size={14} strokeWidth={1.75} />
                  </span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer — light card */}
      <div
        className="mx-3 mb-3"
        style={{
          padding: "10px 12px",
          background: "#F6F8FC",
          border: "1px solid var(--fg-border-soft)",
          borderRadius: 8,
          fontSize: 11,
          lineHeight: "16px",
        }}
      >
        <div
          className="fg-mono"
          style={{ color: "#0F172A", fontWeight: 600 }}
        >
          FileGuard 0.1.0
        </div>
        <div
          style={{ color: "var(--fg-text-2)", marginTop: 1 }}
        >
          Local security console
        </div>
        <div className="flex items-center gap-1.5" style={{ marginTop: 6 }}>
          <span
            className="fg-pulse-dot"
            style={{
              width: 6, height: 6, borderRadius: "50%",
              background: "var(--fg-chart-green)",
              display: "inline-block",
            }}
          />
          <span style={{ color: "var(--fg-text-2)" }}>console ready</span>
        </div>
      </div>
    </aside>
  );
}

export function MobileNav({
  current,
  onChange,
}: {
  current: PageKey;
  onChange: (p: PageKey) => void;
}) {
  return (
    <div
      className="md:hidden flex overflow-x-auto fg-card"
      style={{ padding: 6, gap: 4 }}
    >
      {NAV_ITEMS.map((item) => {
        const Active = current === item.key;
        return (
          <button
            key={item.key}
            onClick={() => onChange(item.key)}
            className="flex-shrink-0 px-3"
            style={{
              height: 32,
              borderRadius: 6,
              background: Active ? "var(--fg-primary-soft)" : "transparent",
              color: Active ? "var(--fg-primary)" : "var(--fg-text-2)",
              fontSize: 12.5,
              fontWeight: Active ? 500 : 400,
              border: 0,
              cursor: "pointer",
              transition: "background-color var(--fg-motion-fast), color var(--fg-motion-fast)",
              whiteSpace: "nowrap",
            }}
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
