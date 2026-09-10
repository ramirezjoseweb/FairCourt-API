import type { MeResponse } from "../api/me";
import type { AppView } from "./AppLayout";
import { Badge, Button, CourtArt, Icon, PageHeader } from "./ui";
import { dateTime } from "../utils/format";
export function DashboardHome({
  me,
  onNavigate,
}: {
  me: MeResponse;
  onNavigate: (view: AppView) => void;
}) {
  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="TU COMUNIDAD, EN MOVIMIENTO"
        title="Qué bien tenerte de vuelta."
        description="Todo listo para disfrutar de los espacios de tu comunidad."
      />
      <section className="home-hero">
        <div className="hero-copy">
          <span className="hero-kicker">
            <span className="status-dot" />
            TUS INSTALACIONES COMUNITARIAS
          </span>
          <h2>
            Haz sitio
            <br />
            para jugar.
          </h2>
          <p>
            Pádel, tenis y mucho más. Encuentra tu momento
            <br className="desktop-only" /> y disfruta de tu comunidad.
          </p>
          <Button className="button-lime" onClick={() => onNavigate("slots")}>
            Encontrar un horario <Icon name="arrow" />
          </Button>
        </div>
        <CourtArt />
      </section>
      <section aria-labelledby="overview-title">
        <div className="section-heading">
          <h2 id="overview-title">Tu vivienda, de un vistazo</h2>
          <span className="muted small">Todo bajo control</span>
        </div>
        <div className="stats-grid">
          <article className="stat-card">
            <div className="stat-top">
              <span>Mi vivienda</span>
              <Icon name="home" />
            </div>
            <strong className="stat-number">
              {me.household_code ?? me.household_id}
            </strong>
            <span className="small muted truncate-email">{me.email}</span>
            <details className="subtle-details">
              <summary>Datos de la vivienda</summary>
              <p>Identificador interno: {me.household_id}</p>
              <p>Correo: {me.email}</p>
            </details>
          </article>
          <article className="stat-card">
            <div className="stat-top">
              <span>Estado de acceso</span>
              <Icon name="shield" />
            </div>
            <strong className="stat-word">
              {me.suspended_until ? "Suspendida" : "Activa"}
            </strong>
            <Badge tone={me.suspended_until ? "red" : "green"}>
              {me.suspended_until ? "Acceso limitado" : "Sin suspensión"}
            </Badge>
            {me.suspended_until && (
              <p className="small muted">
                Hasta {dateTime(me.suspended_until)}
              </p>
            )}
          </article>
          <article className="stat-card">
            <div className="stat-top">
              <span>Penalizaciones</span>
              <Icon name="alert" />
            </div>
            <strong className="stat-number">
              {me.strikes ?? 0}
              <span> strikes</span>
            </strong>
            <span className="small muted">
              {me.strikes
              ? "Consulta el detalle en Auditoría."
                : "Así da gusto compartir espacios."}
            </span>
          </article>
          <article className="stat-card">
            <div className="stat-top">
              <span>Listas de espera</span>
              <Icon name="users" />
            </div>
            <strong className="stat-number">
              {me.active_waitlists_count ?? 0}
              <span> activas</span>
            </strong>
            <span className="small muted">Tus turnos pendientes.</span>
          </article>
        </div>
      </section>
      <div className="home-bottom">
        <section className="panel quick-links">
          <div className="section-heading">
            <h2>Tu próximo paso</h2>
            <Icon name="arrow" />
          </div>
          <button onClick={() => onNavigate("reservations")}>
            <span className="quick-icon">
              <Icon name="ticket" />
            </span>
            <span>
              <strong>Mis reservas</strong>
              <small>Gestiona tus horarios y confirma tu asistencia.</small>
            </span>
            <Icon name="chevron" />
          </button>
          <button onClick={() => onNavigate("notifications")}>
            <span className="quick-icon">
              <Icon name="bell" />
            </span>
            <span>
              <strong>Mantente al día</strong>
              <small>Reservas, turnos y novedades de tu vivienda.</small>
            </span>
            <Icon name="chevron" />
          </button>
        </section>
        <section className="community-card">
          <span className="eyebrow">JUGAR BIEN ES COMPARTIR</span>
          <h2>
            El juego limpio
            <br />
            empieza contigo.
          </h2>
          <p>
            Confirma tu asistencia y libera tu reserva si no puedes venir. Otro
            vecino podrá aprovecharla.
          </p>
          <Button variant="ghost" onClick={() => onNavigate("audit")}>
            Ver mi actividad <Icon name="arrow" />
          </Button>
        </section>
      </div>
    </div>
  );
}
