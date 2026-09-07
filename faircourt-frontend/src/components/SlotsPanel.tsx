import { useCallback } from "react";
import { createReservation, getSlots, joinWaitlist } from "../api/reservations";
import type { Slot } from "../api/reservations";
import { useResource } from "../hooks/useResource";
import { useAction } from "../hooks/useAction";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import {
  dateTime,
  label,
  localDay,
  longDay,
  offsetDay,
  time,
  tone,
} from "../utils/format";
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

export function SlotsPanel({
  day,
  onDayChange,
  refreshKey,
  onChanged,
}: {
  day: string;
  onDayChange: (day: string) => void;
  refreshKey: number;
  onChanged: () => void;
}) {
  const loader = useCallback(() => getSlots(day), [day]);
  const resource = useResource(loader, day, refreshKey);
  const action = useAction();
  const online = useOnlineStatus();
  const slots = [...(resource.data ?? [])].sort((a, b) =>
    a.start_at.localeCompare(b.start_at),
  );
  async function reserve(slot: Slot, waitlist = false) {
    await action.run(
      async () => {
        if (waitlist) await joinWaitlist(slot.start_at);
        else await createReservation(slot.start_at);
        onChanged();
      },
      waitlist
        ? `Te has unido a la lista de espera para el ${dateTime(slot.start_at)}.`
        : `Reserva confirmada para el ${dateTime(slot.start_at)}.`,
    );
  }
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="ENCUENTRA TU MOMENTO"
        title="La pista te espera."
        description="Elige un día y reserva tu próximo rato de deporte."
        action={
          <RefreshButton loading={resource.loading} onClick={resource.reload} />
        }
      />
      <section className="panel agenda-panel">
        <div className="agenda-toolbar">
          <div className="facility">
            <span className="facility-icon">
              <Icon name="court" />
            </span>
            <div>
              <h2>Pista comunitaria</h2>
              <span className="muted small">Un espacio para compartir</span>
            </div>
          </div>
          <label className="date-field">
            Consultar fecha
            <input
              aria-label="Consultar fecha"
              type="date"
              value={day}
              onChange={(event) => {
                if (event.target.value) onDayChange(event.target.value);
              }}
            />
          </label>
        </div>
        <div className="day-selector">
          <Button
            variant="ghost"
            aria-label="Día anterior"
            onClick={() => onDayChange(offsetDay(day, -1))}
          >
            <Icon name="chevron" className="rotate" />
          </Button>
          <div className="day-options">
            {Array.from({ length: 7 }, (_, index) => {
              const date = offsetDay(day, index - 2);
              const dateObj = new Date(`${date}T12:00:00`);
              return (
                <button
                  key={date}
                  aria-pressed={date === day}
                  aria-label={longDay(date)}
                  className={`day-option ${date === day ? "selected" : ""}`}
                  onClick={() => onDayChange(date)}
                >
                  <span>
                    {date === localDay()
                      ? "Hoy"
                      : dateObj
                          .toLocaleDateString("es-ES", { weekday: "short" })
                          .replace(".", "")}
                  </span>
                  <strong>{dateObj.getDate()}</strong>
                  <i />
                </button>
              );
            })}
          </div>
          <Button
            variant="ghost"
            aria-label="Día siguiente"
            onClick={() => onDayChange(offsetDay(day, 1))}
          >
            <Icon name="chevron" />
          </Button>
        </div>
        <div className="agenda-date-heading">
          <h3>{longDay(day)}</h3>
          <Button variant="ghost" onClick={() => onDayChange(localDay())}>
            Volver a hoy
          </Button>
        </div>
        <div className="agenda-legend">
          <span>
            <i className="legend-dot green" />
            Disponible
          </span>
          <span>
            <i className="legend-dot gray" />
            Ocupada
          </span>
          <span>
            <i className="legend-dot lime" />
            Tu reserva
          </span>
          {resource.data && (
            <span className="slots-count">
              {slots.filter((slot) => slot.status === "FREE").length} franjas
              libres
            </span>
          )}
        </div>
        <div className="agenda-content">
          <Feedback error={action.error} message={action.message} />
          <ResourceError error={resource.error} retry={resource.reload} />
          <CacheStamp cacheKey={`faircourt_cache_slots_${day}`} />
          {resource.loading ? (
            <Loading />
          ) : (
            <>
              {!resource.error && slots.length === 0 && (
                <Empty title="No hay franjas para este día">
                  Prueba otra fecha para consultar la disponibilidad.
                </Empty>
              )}
              <div className="slot-list">
                {slots.map((slot) => (
                  <article
                    key={slot.start_at}
                    className={`slot-row ${slot.is_mine ? "slot-mine" : ""}`}
                    aria-label={`Franja ${time(slot.start_at)}`}
                  >
                    <div className="slot-time">
                      <strong>{time(slot.start_at)}</strong>
                      <span>{time(slot.end_at)}</span>
                    </div>
                    <div className="slot-info">
                      <div className="inline-wrap">
                        <Badge tone={tone(slot.status)}>
                          {label(slot.status)}
                        </Badge>
                        {slot.is_mine && (
                          <span className="mine-label">
                            <Icon name="check" />
                            Tu reserva
                          </span>
                        )}
                        {slot.in_waitlist && (
                          <Badge tone="amber">En lista de espera</Badge>
                        )}
                      </div>
                      <p className="small muted waitlist-count">
                        <Icon name="users" />
                        {slot.waitlist_count} en lista de espera
                      </p>
                      {slot.book_reason && !slot.can_book && (
                        <p className="reason">
                          Reserva no disponible: {slot.book_reason}
                        </p>
                      )}
                      {slot.waitlist_reason && !slot.can_join_waitlist && (
                        <p className="reason">
                          Lista de espera: {slot.waitlist_reason}
                        </p>
                      )}
                    </div>
                    <div className="slot-actions">
                      <Button
                        onClick={() => reserve(slot)}
                        disabled={
                          !online ||
                          !slot.can_book ||
                          action.busy ||
                          resource.loading
                        }
                      >
                        Reservar
                        <Icon name="plus" />
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => reserve(slot, true)}
                        disabled={
                          !online ||
                          !slot.can_join_waitlist ||
                          action.busy ||
                          resource.loading
                        }
                      >
                        Lista de espera
                      </Button>
                    </div>
                  </article>
                ))}
              </div>
            </>
          )}
        </div>
      </section>
      <div className="info-strip">
        <Icon name="shield" />
        <p>
          <strong>Las mismas oportunidades para todos.</strong> La
          disponibilidad de cada acción depende de las reglas de reserva de tu
          comunidad.
        </p>
      </div>
    </div>
  );
}
