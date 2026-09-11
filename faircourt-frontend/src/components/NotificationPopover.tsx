import { useEffect, useId, useRef, useState } from "react";
import type { Notification } from "../api/notifications";
import { dateTime, label } from "../utils/format";
import { NotificationEventIcon } from "./NotificationEventIcon";
import { Icon } from "./ui";

const previewLimit = 4;

export function NotificationPopover({
  notifications,
  loading,
  error,
  unreadCount,
  onViewAll,
}: {
  notifications?: Notification[];
  loading: boolean;
  error?: string;
  unreadCount: number;
  onViewAll: () => void;
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const titleId = useId();
  const panelId = useId();
  const rows = [...(notifications ?? [])]
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .slice(0, previewLimit);

  useEffect(() => {
    if (!open) return;

    function closeFromOutside(event: PointerEvent) {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    }

    function closeFromKeyboard(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      setOpen(false);
      buttonRef.current?.focus();
    }

    document.addEventListener("pointerdown", closeFromOutside);
    document.addEventListener("keydown", closeFromKeyboard);
    return () => {
      document.removeEventListener("pointerdown", closeFromOutside);
      document.removeEventListener("keydown", closeFromKeyboard);
    };
  }, [open]);

  return (
    <div className="notification-popover-container" ref={containerRef}>
      <button
        ref={buttonRef}
        type="button"
        className="notification-button"
        aria-label={`Notificaciones, ${unreadCount} sin leer`}
        aria-expanded={open}
        aria-controls={panelId}
        aria-haspopup="dialog"
        onClick={() => setOpen((value) => !value)}
      >
        <Icon name="bell" />
        {unreadCount > 0 && (
          <span className="notification-dot">{unreadCount}</span>
        )}
      </button>
      {open && (
        <section
          id={panelId}
          className="notification-popover"
          role="dialog"
          aria-modal="false"
          aria-labelledby={titleId}
        >
          <header className="notification-popover-heading">
            <div>
              <p className="eyebrow">ACTIVIDAD RECIENTE</p>
              <h2 id={titleId}>Notificaciones</h2>
            </div>
            <span className="notification-popover-count">
              {unreadCount} sin leer
            </span>
          </header>
          <div className="notification-popover-list">
            {loading && !notifications ? (
              <p className="notification-popover-state" role="status">
                Cargando notificaciones…
              </p>
            ) : error && !notifications ? (
              <p className="notification-popover-state" role="alert">
                No se han podido cargar las notificaciones.
              </p>
            ) : !rows.length ? (
              <div className="notification-popover-state">
                <Icon name="bell" />
                <strong>Todo en calma</strong>
                <span>Las novedades de tu vivienda aparecerán aquí.</span>
              </div>
            ) : (
              rows.map((row) => (
                <article
                  key={row.id}
                  className={`notification-preview ${row.is_read ? "" : "unread"}`}
                >
                  <NotificationEventIcon type={row.type} />
                  <div className="notification-preview-content">
                    <div className="notification-preview-title">
                      <h3>{label(row.type)}</h3>
                      {!row.is_read && <span className="unread-label">Nueva</span>}
                    </div>
                    <p>{row.message}</p>
                    <time dateTime={row.created_at}>{dateTime(row.created_at)}</time>
                  </div>
                </article>
              ))
            )}
          </div>
          <button
            type="button"
            className="notification-popover-all"
            onClick={() => {
              setOpen(false);
              onViewAll();
            }}
          >
            Ver todas las notificaciones
            <Icon name="arrow" />
          </button>
        </section>
      )}
    </div>
  );
}
