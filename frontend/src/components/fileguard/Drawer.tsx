import { ReactNode, useEffect, useState } from "react";
import { X } from "lucide-react";

export function DetailDrawer({
  open,
  onClose,
  title,
  subtitle,
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  subtitle?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
}) {
  const [mounted, setMounted] = useState(open);

  useEffect(() => {
    if (open) setMounted(true);
    else {
      const t = setTimeout(() => setMounted(false), 200);
      return () => clearTimeout(t);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!mounted) return null;

  return (
    <div aria-hidden={!open}>
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 40,
          background: "rgba(15, 23, 42, 0.32)",
          backdropFilter: "blur(2px)",
          opacity: open ? 1 : 0,
          transition: "opacity var(--fg-motion)",
        }}
      />
      <aside
        role="dialog"
        aria-modal="true"
        style={{
          position: "fixed",
          top: 12,
          right: 12,
          bottom: 12,
          width: "min(480px, calc(100vw - 24px))",
          zIndex: 50,
          background: "var(--fg-panel)",
          boxShadow: "var(--fg-shadow-float)",
          borderRadius: 12,
          border: "1px solid var(--fg-hairline)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          opacity: open ? 1 : 0,
          transform: open ? "translateX(0)" : "translateX(24px)",
          transition:
            "transform var(--fg-motion), opacity var(--fg-motion)",
        }}
      >
        <header
          className="flex items-start justify-between px-5"
          style={{
            paddingTop: 14,
            paddingBottom: 12,
            borderBottom: "1px solid var(--fg-border-soft)",
            gap: 12,
          }}
        >
          <div>
            <div
              style={{
                color: "var(--fg-text)",
                fontSize: 15,
                fontWeight: 600,
                lineHeight: "20px",
              }}
            >
              {title}
            </div>
            {subtitle && (
              <div
                className="mt-1 flex items-center gap-1.5 fg-mono"
                style={{ color: "var(--fg-text-3)", fontSize: 11 }}
              >
                {subtitle}
              </div>
            )}
          </div>
          <div className="flex items-center gap-1.5">
            <span className="fg-kbd">Esc</span>
            <button
              onClick={onClose}
              className="fg-icon-btn"
              aria-label="关闭"
            >
              <X size={15} />
            </button>
          </div>
        </header>
        <div
          className="flex-1 overflow-y-auto"
          style={{ padding: "16px 20px 24px" }}
        >
          {children}
        </div>
        {footer && (
          <footer
            style={{
              padding: "10px 16px",
              borderTop: "1px solid var(--fg-border-soft)",
              background: "#FAFCFE",
            }}
          >
            {footer}
          </footer>
        )}
      </aside>
    </div>
  );
}
