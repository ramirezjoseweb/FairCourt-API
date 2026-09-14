import { useEffect, useId, useRef } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export type IconName =
  | "court"
  | "home"
  | "calendar"
  | "ticket"
  | "bell"
  | "history"
  | "unlock"
  | "logout"
  | "arrow"
  | "chevron"
  | "refresh"
  | "check"
  | "clock"
  | "users"
  | "more"
  | "close"
  | "wifi"
  | "shield"
  | "mail"
  | "copy"
  | "external"
  | "plus"
  | "alert"
  | "moon"
  | "sun";
const paths: Record<IconName, ReactNode> = {
  court: (
    <>
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M3 12h18M7 3v18M17 3v18M7 7h10M7 17h10M12 7v10" />
    </>
  ),
  home: (
    <>
      <path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1Z" />
      <path d="M9 21v-8h6v8" />
    </>
  ),
  calendar: (
    <>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M7 3v4m10-4v4M3 11h18m-13 4h2m4 0h2" />
    </>
  ),
  ticket: (
    <>
      <path d="M4 4h16v6a2 2 0 0 0 0 4v6H4v-6a2 2 0 0 0 0-4Z" />
      <path d="M9 8h6m-6 4h4m-4 4h6" />
    </>
  ),
  bell: (
    <>
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
    </>
  ),
  history: (
    <>
      <path d="M3 11a9 9 0 1 1 2 7M3 4v7h7M12 7v5l3 2" />
    </>
  ),
  unlock: (
    <>
      <rect x="4" y="10" width="16" height="11" rx="2" />
      <path d="M8 10V6a4 4 0 0 1 8 0m-4 8v3" />
    </>
  ),
  logout: (
    <>
      <path d="M9 3H4v18h5m6-14 5 5-5 5m-7-5h12" />
    </>
  ),
  arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
  chevron: <path d="m9 5 7 7-7 7" />,
  refresh: (
    <>
      <path d="M20 7a9 9 0 0 0-15-2L2 8m0-6v6h6M4 17a9 9 0 0 0 15 2l3-3m0 6v-6h-6" />
    </>
  ),
  check: <path d="m5 12 4 4L19 6" />,
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 6v6l4 2" />
    </>
  ),
  users: (
    <>
      <circle cx="9" cy="7" r="3" />
      <path d="M3 21v-4a6 6 0 0 1 12 0v4m1-17a3 3 0 0 1 0 6m2 3a5 5 0 0 1 3 4v4" />
    </>
  ),
  more: (
    <>
      <circle cx="5" cy="12" r="1" />
      <circle cx="12" cy="12" r="1" />
      <circle cx="19" cy="12" r="1" />
    </>
  ),
  close: <path d="m6 6 12 12M6 18 18 6" />,
  wifi: (
    <>
      <path d="M2 8a16 16 0 0 1 20 0M5 12a11 11 0 0 1 14 0m-11 4a6 6 0 0 1 8 0" />
      <circle cx="12" cy="20" r=".5" />
    </>
  ),
  shield: (
    <>
      <path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6Z" />
      <path d="m8 12 3 3 5-6" />
    </>
  ),
  mail: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="m3 6 9 7 9-7" />
    </>
  ),
  copy: (
    <>
      <rect x="8" y="8" width="13" height="13" rx="2" />
      <path d="M16 8V3H3v13h5" />
    </>
  ),
  external: (
    <>
      <path d="M14 3h7v7m0-7L10 14M10 3H3v18h18v-7" />
    </>
  ),
  plus: <path d="M12 4v16M4 12h16" />,
  alert: (
    <>
      <path d="m12 3 10 18H2Z" />
      <path d="M12 9v5m0 3v.5" />
    </>
  ),
  moon: <path d="M20.5 15.1A9 9 0 0 1 8.9 3.5 9 9 0 1 0 20.5 15.1Z" />,
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </>
  ),
};
export function Icon({
  name,
  className = "",
}: {
  name: IconName;
  className?: string;
}) {
  return (
    <svg
      className={`icon ${className}`}
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}
export function Brand() {
  return (
    <span className="brand">
      <span className="brand-mark">
        <Icon name="court" />
      </span>
      <span>
        faircourt<span className="brand-dot">.</span>
      </span>
    </span>
  );
}
export function Button({
  children,
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
}) {
  return (
    <button
      type="button"
      className={`button button-${variant} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function ThemeToggle({
  theme,
  onToggle,
  className = "",
}: {
  theme: "light" | "dark";
  onToggle: () => void;
  className?: string;
}) {
  const dark = theme === "dark";
  const label = dark ? "Activar modo claro" : "Activar modo oscuro";
  return (
    <button
      type="button"
      className={`theme-toggle ${className}`}
      onClick={onToggle}
      aria-label={label}
      title={label}
    >
      <Icon name={dark ? "sun" : "moon"} />
    </button>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "green" | "amber" | "red" | "neutral";
}) {
  return (
    <span className={`badge badge-${tone}`}>
      <span className="status-dot" />
      {children}
    </span>
  );
}
export function Notice({
  children,
  kind = "success",
}: {
  children?: ReactNode;
  kind?: "success" | "error" | "info";
}) {
  if (!children) return null;
  return (
    <div
      className={`notice notice-${kind}`}
      role={kind === "error" ? "alert" : "status"}
    >
      <Icon
        name={
          kind === "error" ? "alert" : kind === "success" ? "check" : "wifi"
        }
      />
      <div>{children}</div>
    </div>
  );
}
export function Feedback({
  error,
  message,
}: {
  error?: string;
  message?: string;
}) {
  return (
    <>
      <Notice kind="error">{error}</Notice>
      <Notice>{message}</Notice>
    </>
  );
}
export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <header className="page-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="muted">{description}</p>
      </div>
      {action}
    </header>
  );
}
export function RefreshButton({
  loading,
  onClick,
}: {
  loading: boolean;
  onClick: () => void;
}) {
  return (
    <Button variant="secondary" disabled={loading} onClick={onClick}>
      <Icon name="refresh" className={loading ? "spin" : ""} />
      {loading ? "Actualizando…" : "Actualizar"}
    </Button>
  );
}
export function Empty({
  icon = "calendar",
  title,
  children,
}: {
  icon?: IconName;
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <Icon name={icon} />
      </span>
      <h3>{title}</h3>
      <p className="muted">{children}</p>
    </div>
  );
}
export function Loading() {
  return (
    <div className="loading-state" role="status">
      <span className="loader" />
      <span>Cargando información…</span>
    </div>
  );
}
export function ResourceError({
  error,
  retry,
}: {
  error?: string;
  retry: () => void;
}) {
  return error ? (
    <Notice kind="error">
      <p>{error}</p>
      <Button variant="ghost" onClick={retry}>
        Reintentar <Icon name="refresh" />
      </Button>
    </Notice>
  ) : null;
}
export function Dialog({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const id = useId();
  useEffect(() => {
    const dialog = ref.current!;
    const previous = document.activeElement as HTMLElement | null;
    dialog.showModal();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      dialog.close();
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, []);
  return (
    <dialog
      className="dialog"
      ref={ref}
      aria-labelledby={id}
      onKeyDown={(event) => {
        if (event.key !== "Tab") return;
        const controls = Array.from(
          ref.current!.querySelectorAll<HTMLElement>(
            'button:not(:disabled), a[href], input:not(:disabled), textarea:not(:disabled), select:not(:disabled), [tabindex="0"]',
          ),
        ).filter((element) => element.getClientRects().length > 0);
        const first = controls[0],
          last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === ref.current) {
          const box = ref.current.getBoundingClientRect();
          if (
            event.clientX < box.left ||
            event.clientX > box.right ||
            event.clientY < box.top ||
            event.clientY > box.bottom
          )
            onClose();
        }
      }}
    >
      <div className="dialog-heading">
        <h2 id={id}>{title}</h2>
        <Button variant="ghost" aria-label="Cerrar diálogo" onClick={onClose}>
          <Icon name="close" />
        </Button>
      </div>
      {children}
    </dialog>
  );
}
export function CourtArt({ className = "" }: { className?: string }) {
  return (
    <div className={`court-art ${className}`} aria-hidden="true">
      <div className="court-orbit" />
      <div className="court-surface">
        <div className="court-lines">
          <i />
          <b />
          <em />
        </div>
        <span className="court-ball" />
      </div>
      <span className="court-caption">EL DEPORTE NOS ENCUENTRA.</span>
    </div>
  );
}
