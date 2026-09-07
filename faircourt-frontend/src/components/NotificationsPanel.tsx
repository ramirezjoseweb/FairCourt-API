import type { Notification } from "../api/notifications";
import { markNotificationAsRead } from "../api/notifications";
import { saveToCache } from "../utils/offlineCache";
import { useAction } from "../hooks/useAction";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import { dateTime, label, tone } from "../utils/format";
import {
  Badge,
  Button,
  Empty,
  Feedback,
  Icon,
  Loading,
  PageHeader,
  RefreshButton,
  ResourceError,
} from "./ui";
import { CacheStamp } from "./CacheStamp";
export function NotificationsPanel({
  resource,
  onChanged,
}: {
  resource: {
    data?: Notification[];
    loading: boolean;
    error?: string;
    reload: () => void;
  };
  onChanged: () => void;
}) {
  const action = useAction();
  const online = useOnlineStatus();
  const rows = [...(resource.data ?? [])].sort((a, b) =>
    b.created_at.localeCompare(a.created_at),
  );
  const unread = rows.filter((row) => !row.is_read).length;
  async function read(row: Notification) {
    await action.run(async () => {
      const updated = await markNotificationAsRead(row.id);
      saveToCache(
        "faircourt_cache_notifications",
        rows.map((item) => (item.id === updated.id ? updated : item)),
      );
      onChanged();
    }, "Notificación marcada como leída.");
  }
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="AL DÍA CON TU COMUNIDAD"
        title="Tus notificaciones."
        description="Los avisos que importan, en un mismo lugar."
        action={
          <RefreshButton loading={resource.loading} onClick={resource.reload} />
        }
      />
      <Feedback error={action.error} message={action.message} />
      <ResourceError error={resource.error} retry={resource.reload} />
      <CacheStamp cacheKey="faircourt_cache_notifications" />
      <section className="panel inbox">
        <div className="inbox-heading">
          <h2>Bandeja de entrada</h2>
          <Badge tone={unread ? "green" : "neutral"}>{unread} sin leer</Badge>
        </div>
        {resource.loading && !resource.data ? (
          <Loading />
        ) : !rows.length && !resource.error ? (
          <Empty icon="bell" title="Todo en calma">
            Cuando haya novedades sobre tu vivienda, aparecerán aquí.
          </Empty>
        ) : (
          rows.map((row) => (
            <article
              key={row.id}
              className={`notification-row ${row.is_read ? "" : "unread"}`}
              aria-label={`Notificación #${row.id}`}
            >
              <span className={`event-icon event-${tone(row.type)}`}>
                <Icon
                  name={
                    row.type.includes("WAITLIST")
                      ? "users"
                      : row.type.includes("SUSPENDED") || row.type === "NO_SHOW"
                        ? "alert"
                        : "bell"
                  }
                />
              </span>
              <div className="notification-content">
                <div className="inline-wrap">
                  <h3>{label(row.type)}</h3>
                  {!row.is_read && <span className="unread-label">Nueva</span>}
                </div>
                <p>{row.message}</p>
                <time className="small muted" dateTime={row.created_at}>
                  {dateTime(row.created_at)}
                </time>
              </div>
              <Button
                variant="secondary"
                disabled={!online || row.is_read || action.busy}
                onClick={() => read(row)}
              >
                <Icon name="check" />
                {row.is_read ? "Leída" : "Marcar leída"}
              </Button>
            </article>
          ))
        )}
      </section>
    </div>
  );
}
