import { getMyAuditLog } from "../api/audit";
import { useResource } from "../hooks/useResource";
import { dateTime, label, tone } from "../utils/format";
import {
  Badge,
  Empty,
  Icon,
  Loading,
  PageHeader,
  RefreshButton,
  ResourceError,
} from "./ui";
import { CacheStamp } from "./CacheStamp";
function metadata(raw: string | null) {
  if (!raw) return null;
  try {
    const value: unknown = JSON.parse(raw);
    if (value && typeof value === "object")
      return (
        <dl className="metadata-grid">
          {Object.entries(value).map(([key, item]) => (
            <div key={key}>
              <dt>{key}</dt>
              <dd>
                {item === null
                  ? "—"
                  : typeof item === "object"
                    ? JSON.stringify(item)
                    : String(item)}
              </dd>
            </div>
          ))}
        </dl>
      );
  } catch {
    /* Preserve unfamiliar payloads as readable text. */
  }
  return <pre className="raw-metadata">{raw}</pre>;
}
export function AuditPanel({ refreshKey }: { refreshKey: number }) {
  const resource = useResource(getMyAuditLog, "audit", refreshKey);
  const rows = [...(resource.data ?? [])].sort((a, b) =>
    b.created_at.localeCompare(a.created_at),
  );
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="CLARIDAD PARA TODOS"
        title="Tu actividad, transparente."
        description="Un registro de lo que ocurre en tu vivienda. Cada acción tiene su historia."
        action={
          <RefreshButton loading={resource.loading} onClick={resource.reload} />
        }
      />
      <ResourceError error={resource.error} retry={resource.reload} />
      <CacheStamp cacheKey="faircourt_cache_audit" />
      <section className="panel audit-panel">
        <div className="section-heading">
          <h2>Registro de actividad</h2>
          <Icon name="history" />
        </div>
        {resource.loading && !resource.data ? (
          <Loading />
        ) : !rows.length && !resource.error ? (
          <Empty icon="history" title="Todavía no hay actividad">
            Tus reservas, accesos y eventos de comunidad quedarán registrados
            aquí.
          </Empty>
        ) : (
          <div className="timeline">
            {rows.map((row) => (
              <article className="timeline-item" key={row.id}>
                <span className={`event-icon event-${tone(row.event)}`}>
                  <Icon
                    name={
                      row.event.includes("CHECKIN")
                        ? "check"
                        : row.event.includes("UNLOCK")
                          ? "unlock"
                          : "history"
                    }
                  />
                </span>
                <div className="timeline-content">
                  <div className="timeline-title">
                    <h3>{label(row.event)}</h3>
                    <time dateTime={row.created_at}>
                      {dateTime(row.created_at)}
                    </time>
                  </div>
                  {row.reservation_id != null && (
                    <Badge>Reserva #{row.reservation_id}</Badge>
                  )}
                  <details className="audit-details">
                    <summary>Ver detalles del evento</summary>
                    <dl className="metadata-grid">
                      <div>
                        <dt>ID del evento</dt>
                        <dd>#{row.id}</dd>
                      </div>
                      <div>
                        <dt>Código del evento</dt>
                        <dd>{row.event}</dd>
                      </div>
                      <div>
                        <dt>Vivienda</dt>
                        <dd>{row.household_id ?? "—"}</dd>
                      </div>
                      <div>
                        <dt>Usuario</dt>
                        <dd>{row.user_id ?? "—"}</dd>
                      </div>
                    </dl>
                    {metadata(row.metadata_json)}
                  </details>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
      <div className="info-strip">
        <Icon name="shield" />
        <p>La transparencia también forma parte del juego limpio.</p>
      </div>
    </div>
  );
}
