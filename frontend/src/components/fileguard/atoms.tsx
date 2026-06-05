import { ReactNode, useState } from "react";
import { normalizeLevel, RISK_COLORS, RiskLevel, scoreToLevel, scoreToPercent, truncatePath } from "./data";
import { Copy, Check } from "lucide-react";

/* ----------------------------------------------------------------
 * Risk badge — unified visual system
 * ---------------------------------------------------------------- */
export function RiskBadge({ level, dense }: { level: RiskLevel | null | undefined; dense?: boolean }) {
  const normalized = normalizeLevel(level === "UNKNOWN" ? undefined : level);
  const c = RISK_COLORS[normalized] ?? RISK_COLORS.UNKNOWN;
  return (
    <span
      className="fg-risk"
      style={{
        color: c.fg,
        background: c.bg,
        borderColor: c.fg + "33",
        padding: dense ? "1px 6px 1px 5px" : undefined,
        fontSize: dense ? 11 : 11.5,
      }}
    >
      <span className="fg-risk-dot" />
      {c.label}
    </span>
  );
}

export function StatusDot({ on, color, pulse }: { on: boolean; color?: string; pulse?: boolean }) {
  return (
    <span
      className={pulse && on ? "fg-pulse-dot" : ""}
      style={{
        display: "inline-block",
        width: 8,
        height: 8,
        borderRadius: "50%",
        background: on ? color ?? "var(--fg-success)" : "#94A3B8",
      }}
    />
  );
}

/* ----------------------------------------------------------------
 * Cards
 * ---------------------------------------------------------------- */
export function StatCard({
  label,
  value,
  sub,
  icon,
  trend,
  tone = "primary",
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  icon?: ReactNode;
  trend?: number[];
  tone?: "primary" | "neutral";
}) {
  return (
    <div className="fg-card fg-stat" style={{ padding: 16 }}>
      <div className="flex items-start justify-between mb-2">
        <span
          style={{
            color: "var(--fg-text-2)",
            fontSize: 11.5,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            fontWeight: 500,
          }}
        >
          {label}
        </span>
        {icon && (
          <span
            className="flex items-center justify-center"
            style={{
              width: 26,
              height: 26,
              borderRadius: 6,
              background: tone === "primary" ? "var(--fg-primary-soft)" : "#F1F5F9",
              color: tone === "primary" ? "var(--fg-primary)" : "var(--fg-text-2)",
              border: "1px solid",
              borderColor: tone === "primary" ? "#D6E2FB" : "#E2E8F0",
            }}
          >
            {icon}
          </span>
        )}
      </div>
      <div
        className="fg-num"
        style={{ color: "var(--fg-text)", fontSize: 22, lineHeight: "30px", fontWeight: 600 }}
      >
        {value}
      </div>
      {sub && (
        <div
          style={{
            color: "var(--fg-text-2)",
            fontSize: 12,
            marginTop: 2,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          {sub}
        </div>
      )}
      {trend && trend.length > 0 && (
        <Sparkline values={trend} />
      )}
    </div>
  );
}

export function Sparkline({ values, color }: { values: number[]; color?: string }) {
  const max = Math.max(...values, 1);
  return (
    <div className="flex items-end gap-[2px] mt-3" style={{ height: 18 }}>
      {values.map((v, i) => (
        <span
          key={i}
          style={{
            flex: 1,
            height: `${(v / max) * 100}%`,
            minHeight: 2,
            background: color ?? "var(--fg-primary)",
            opacity: 0.25 + (i / values.length) * 0.6,
            borderRadius: 1,
          }}
        />
      ))}
    </div>
  );
}

export function ContentCard({
  title,
  subtitle,
  extra,
  children,
  padding = true,
}: {
  title?: ReactNode;
  subtitle?: ReactNode;
  extra?: ReactNode;
  children: ReactNode;
  padding?: boolean;
}) {
  return (
    <section className="fg-card">
      {(title || extra) && (
        <header className="fg-card-header">
          <div>
            {title && <div className="fg-card-title">{title}</div>}
            {subtitle && <div className="fg-card-subtitle">{subtitle}</div>}
          </div>
          {extra && <div className="flex items-center gap-2">{extra}</div>}
        </header>
      )}
      <div className={padding ? "fg-card-body" : ""}>{children}</div>
    </section>
  );
}

/* ----------------------------------------------------------------
 * Path cell with tooltip via title attr
 * ---------------------------------------------------------------- */
export function PathCell({ path, max = 56 }: { path: string | null; max?: number }) {
  if (!path) return <span style={{ color: "var(--fg-text-3)" }}>—</span>;
  return (
    <span
      title={path}
      className="fg-mono"
      style={{ color: "var(--fg-text)", fontSize: 12 }}
    >
      {truncatePath(path, max)}
    </span>
  );
}

/* ----------------------------------------------------------------
 * Score meter
 * ---------------------------------------------------------------- */
export function ScoreMeter({ score }: { score: number | null | undefined }) {
  const level = scoreToLevel(score);
  const c = RISK_COLORS[level];
  return (
    <div className="flex items-center gap-2.5" style={{ minWidth: 130 }}>
      <div className="fg-meter" style={{ flex: 1 }}>
        <span style={{ width: `${scoreToPercent(score)}%`, background: c.fg }} />
      </div>
      <span
        className="fg-num"
        style={{ fontSize: 12, color: "var(--fg-text)", minWidth: 24, textAlign: "right", fontWeight: 600 }}
      >
        {typeof score === "number" ? score.toFixed(2) : "—"}
      </span>
    </div>
  );
}

/* ----------------------------------------------------------------
 * Chip — small tag
 * ---------------------------------------------------------------- */
export function Chip({
  children,
  color = "#475569",
  bg = "#F1F5F9",
  border,
  mono,
}: {
  children: ReactNode;
  color?: string;
  bg?: string;
  border?: string;
  mono?: boolean;
}) {
  return (
    <span
      className={mono ? "fg-mono" : ""}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        height: 20,
        padding: "0 7px",
        borderRadius: 4,
        background: bg,
        color,
        border: `1px solid ${border ?? "transparent"}`,
        fontSize: 11.5,
        lineHeight: 1,
        fontWeight: 500,
      }}
    >
      {children}
    </span>
  );
}

/* ----------------------------------------------------------------
 * Code / JSON
 * ---------------------------------------------------------------- */
export function JsonCodeBlock({ data, label }: { data: unknown; label?: string }) {
  return (
    <div>
      {label && (
        <div className="fg-mono flex items-center justify-between mb-1.5" style={{ fontSize: 11 }}>
          <span style={{ color: "var(--fg-text-3)", letterSpacing: "0.06em", textTransform: "uppercase" }}>
            {label}
          </span>
          <span style={{ color: "var(--fg-text-3)" }}>json</span>
        </div>
      )}
      <pre className="fg-code">{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}

/* ----------------------------------------------------------------
 * Buttons (kept for compatibility; CSS classes also available)
 * ---------------------------------------------------------------- */
export function PrimaryButton({
  children,
  onClick,
  loading,
  disabled,
  icon,
}: {
  children: ReactNode;
  onClick?: () => void;
  loading?: boolean;
  disabled?: boolean;
  icon?: ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className="fg-btn fg-btn-primary"
    >
      {loading && (
        <span
          aria-hidden
          style={{
            display: "inline-block",
            width: 12,
            height: 12,
            borderRadius: "50%",
            border: "2px solid white",
            borderTopColor: "transparent",
            animation: "spin 0.7s linear infinite",
          }}
        />
      )}
      {!loading && icon}
      {children}
    </button>
  );
}

export function SecondaryButton({
  children,
  onClick,
  icon,
}: {
  children: ReactNode;
  onClick?: () => void;
  icon?: ReactNode;
  active?: boolean;
}) {
  return (
    <button onClick={onClick} className="fg-btn fg-btn-secondary">
      {icon}
      {children}
    </button>
  );
}

export function GhostLink({
  children,
  onClick,
  icon,
}: {
  children: ReactNode;
  onClick?: () => void;
  icon?: ReactNode;
}) {
  return (
    <button onClick={onClick} className="fg-btn fg-btn-ghost">
      {children}
      <span className="fg-arrow" style={{ display: "inline-flex" }}>{icon}</span>
    </button>
  );
}

export function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard?.writeText(text).catch(() => {});
        setCopied(true);
        setTimeout(() => setCopied(false), 1200);
      }}
      title="复制"
      aria-label="复制"
      className="fg-icon-btn"
    >
      {copied ? <Check size={14} color="var(--fg-success)" /> : <Copy size={14} />}
    </button>
  );
}

/* ----------------------------------------------------------------
 * Empty state — refined
 * ---------------------------------------------------------------- */
export function EmptyState({
  title,
  desc,
  icon,
  action,
}: {
  title: string;
  desc?: string;
  icon?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-12 px-6">
      <div
        className="flex items-center justify-center mb-3"
        style={{
          width: 44,
          height: 44,
          borderRadius: 10,
          background: "#F1F5F9",
          border: "1px solid #E2E8F0",
          color: "var(--fg-text-2)",
        }}
      >
        {icon ?? <DashIcon />}
      </div>
      <div style={{ color: "var(--fg-text)", fontSize: 13.5, fontWeight: 600, marginBottom: 3 }}>
        {title}
      </div>
      {desc && (
        <div style={{ color: "var(--fg-text-2)", fontSize: 12, maxWidth: 380, lineHeight: "18px" }}>
          {desc}
        </div>
      )}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}

function DashIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M5 12h14" strokeDasharray="2 3" />
      <circle cx="12" cy="12" r="9" strokeDasharray="3 3" opacity="0.4" />
    </svg>
  );
}

/* ----------------------------------------------------------------
 * Section heading inside drawer/card
 * ---------------------------------------------------------------- */
export function FieldLabel({ children }: { children: ReactNode }) {
  return (
    <div
      className="fg-mono"
      style={{
        color: "var(--fg-text-3)",
        fontSize: 10.5,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        marginBottom: 4,
      }}
    >
      {children}
    </div>
  );
}
