import { useEffect, useState } from "react";
import {
  cancelReservation,
  getMyReservations,
  getCheckinQr,
} from "../api/reservations";
import type { Reservation, CheckinQrResponse } from "../api/reservations";
import { useResource } from "../hooks/useResource";
import { useAction } from "../hooks/useAction";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import { dateTime, label, time, tone } from "../utils/format";
import {
  Badge,
  Button,
  Dialog,
  Empty,
  Feedback,
  Icon,
  Loading,
  PageHeader,
  RefreshButton,
  ResourceError,
} from "./ui";
import { CacheStamp } from "./CacheStamp";
export function MyReservationsPanel({
  refreshKey,
  onChanged,
}: {
  refreshKey: number;
  onChanged: () => void;
}) {
  const resource = useResource(getMyReservations, "reservations", refreshKey);
  const action = useAction();
  const online = useOnlineStatus();
  const [cancel, setCancel] = useState<Reservation | null>(null);
  const [checkin, setCheckin] = useState<CheckinQrResponse | null>(null);
  const [copyMessage, setCopyMessage] = useState("");
  const [copyError, setCopyError] = useState("");
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 60000);
    return () => window.clearInterval(timer);
  }, []);
  const rows = resource.data ?? [];
  const upcoming = rows
    .filter(
      (row) =>
        (row.real_status || row.status) === "ACTIVE" &&
        new Date(row.end_at).getTime() > now,
    )
    .sort((a, b) => a.start_at.localeCompare(b.start_at));
  const upcomingIds = new Set(upcoming.map((row) => row.id));
  const history = rows
    .filter((row) => !upcomingIds.has(row.id))
    .sort((a, b) => b.start_at.localeCompare(a.start_at));
  async function confirmCancel() {
    if (!cancel) return;
    const success = await action.run(async () => {
      await cancelReservation(cancel.id);
      onChanged();
    }, "Reserva cancelada. Gracias por dejar sitio a otro vecino.");
    if (success) setCancel(null);
  }
  async function requestCheckin(reservation: Reservation) {
    await action.run(async () => {
      const data = await getCheckinQr(reservation.id);
      setCopyMessage("");
      setCopyError("");
      setCheckin(data);
    });
  }
  async function copy() {
    if (!checkin) return;
    try {
      await navigator.clipboard.writeText(checkin.checkin_url);
      setCopyMessage("Enlace copiado.");
      setCopyError("");
    } catch {
      setCopyError(
        "No se pudo copiar. Puedes seleccionar y copiar el enlace de abajo.",
      );
    }
  }
  function reservationCard(row: Reservation) {
    const status = row.real_status || row.status;
    const date = new Date(row.start_at);
    return (
      <article
        className="reservation-card"
        key={row.id}
        aria-label={`Reserva #${row.id}`}
      >
        <div className="reservation-date">
          <span>
            {date
              .toLocaleDateString("es-ES", { month: "short" })
              .replace(".", "")}
          </span>
          <strong>{date.getDate()}</strong>
          <small>{date.getFullYear()}</small>
        </div>
        <div className="reservation-info">
          <div className="inline-wrap">
            <h3>Pista comunitaria</h3>
            <Badge tone={tone(status)}>{label(status)}</Badge>
          </div>
          <p className="reservation-time">
            <Icon name="clock" />
            {time(row.start_at)} — {time(row.end_at)}
          </p>
          <p className="small muted">
            {dateTime(row.start_at)} · Hasta {dateTime(row.end_at)}
          </p>
          <details className="subtle-details">
            <summary>Detalles de la reserva</summary>
            <p>
              Reserva #{row.id} · Estado registrado: {label(row.status)} (
              {row.status})
            </p>
            <p>
              Estado actual: {label(status)} ({status})
            </p>
          </details>
        </div>
        <div className="reservation-actions">
          <Button
            disabled={!online || status !== "ACTIVE" || action.busy}
            onClick={() => requestCheckin(row)}
          >
            <Icon name="check" />
            Check-in
          </Button>
          <Button
            variant="ghost"
            className="text-danger"
            disabled={!online || status !== "ACTIVE" || action.busy}
            onClick={() => setCancel(row)}
          >
            Cancelar reserva
          </Button>
        </div>
      </article>
    );
  }
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="TU TIEMPO EN LA PISTA"
        title="Mis reservas."
        description="Tus próximos encuentros y todas las veces que has formado parte del juego."
        action={
          <RefreshButton loading={resource.loading} onClick={resource.reload} />
        }
      />
      <Feedback
        error={cancel ? undefined : action.error}
        message={action.message}
      />
      <ResourceError error={resource.error} retry={resource.reload} />
      <CacheStamp cacheKey="faircourt_cache_reservations" />
      {resource.loading && !resource.data ? (
        <Loading />
      ) : resource.error && !resource.data ? null : (
        <>
          <section>
            <div className="section-heading">
              <h2>
                Próximas reservas{" "}
                <span className="section-count">{upcoming.length}</span>
              </h2>
              <span className="small muted">Nos vemos en la pista</span>
            </div>
            <div className="reservation-list">
              {upcoming.length ? (
                upcoming.map(reservationCard)
              ) : (
                <div className="panel">
                  <Empty
                    icon="ticket"
                    title="Tu próxima partida está por llegar"
                  >
                    Consulta Disponibilidad para encontrar tu horario.
                  </Empty>
                </div>
              )}
            </div>
          </section>
          <section>
            <div className="section-heading">
              <h2>
                Historial{" "}
                <span className="section-count">{history.length}</span>
              </h2>
            </div>
            <div className="reservation-list">
              {history.length ? (
                history.map(reservationCard)
              ) : (
                <div className="panel">
                  <Empty icon="history" title="Una historia por empezar">
                    Aquí encontrarás tus reservas pasadas y canceladas.
                  </Empty>
                </div>
              )}
            </div>
          </section>
        </>
      )}
      {cancel && (
        <Dialog
          title="¿Liberar tu reserva?"
          onClose={() => {
            if (!action.busy) setCancel(null);
          }}
        >
          <div className="dialog-emblem">
            <Icon name="calendar" />
          </div>
          <p>Vas a cancelar tu reserva de la pista comunitaria.</p>
          <div className="dialog-summary">
            <strong>{dateTime(cancel.start_at)}</strong>
            <span>Hasta {dateTime(cancel.end_at)}</span>
          </div>
          <p className="muted">
            La franja quedará disponible para tu comunidad. Esta acción no se
            puede deshacer.
          </p>
          <Feedback error={action.error} />
          <div className="dialog-actions">
            <Button
              variant="secondary"
              disabled={action.busy}
              onClick={() => setCancel(null)}
            >
              Mantener reserva
            </Button>
            <Button
              variant="danger"
              disabled={action.busy || !online}
              onClick={confirmCancel}
            >
              {action.busy ? "Cancelando…" : "Sí, cancelar reserva"}
            </Button>
          </div>
        </Dialog>
      )}
      {checkin && (
        <Dialog title="Confirma tu asistencia" onClose={() => setCheckin(null)}>
          <div className="dialog-emblem">
            <Icon name="check" />
          </div>
          <p>
            Enlace de check-in para la reserva{" "}
            <strong>#{checkin.reservation_id}</strong>.
          </p>
          <p className="muted">
            Abre el enlace para confirmar tu asistencia dentro del horario
            permitido.
          </p>
          <div className="dialog-summary">
            <span>El enlace expira</span>
            <strong>{dateTime(checkin.expires_at)}</strong>
          </div>
          <a
            className={`button button-primary full-width ${!online ? "link-disabled" : ""}`}
            aria-disabled={!online}
            tabIndex={online ? 0 : -1}
            href={online ? checkin.checkin_url : undefined}
            target="_blank"
            rel="noreferrer"
          >
            Abrir check-in
            <Icon name="external" />
          </a>
          <Button variant="secondary" className="full-width" onClick={copy}>
            <Icon name="copy" />
            Copiar enlace
          </Button>
          <Feedback message={copyMessage} error={copyError} />
          <label className="checkin-link-label" htmlFor="checkin-link">
            Enlace de asistencia
          </label>
          <input id="checkin-link" readOnly value={checkin.checkin_url} />
        </Dialog>
      )}
    </div>
  );
}
