import { useState } from "react";
import {
  getAdminCommunities,
  getAdminCommunityAudit,
  getAdminCommunityPolicy,
  getAdminMe,
  requestAdminOtp,
  selectAdminCommunity,
  verifyAdminOtp,
} from "../api/admin";
import type {
  AdminAuditEntry,
  CommunityPolicy,
  CommunitySummary,
} from "../api/admin";
import { useAction } from "../hooks/useAction";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import { useResource } from "../hooks/useResource";
import type { Theme } from "../hooks/useTheme";
import {
  Badge,
  Brand,
  Button,
  Feedback,
  Icon,
  Loading,
  Notice,
  ResourceError,
  ThemeToggle,
} from "./ui";

export function AdminApp({
  theme,
  onToggleTheme,
}: {
  theme: Theme;
  onToggleTheme: () => void;
}) {
  const [token, setToken] = useState(() =>
    localStorage.getItem("faircourt_admin_token"),
  );
  function logout() {
    localStorage.removeItem("faircourt_admin_token");
    setToken(null);
  }
  return token ? (
    <AdminDashboard
      onLogout={logout}
      theme={theme}
      onToggleTheme={onToggleTheme}
    />
  ) : (
    <AdminLogin
      onAuthenticated={(value) => {
        localStorage.setItem("faircourt_admin_token", value);
        setToken(value);
      }}
      theme={theme}
      onToggleTheme={onToggleTheme}
    />
  );
}

function AdminLogin({
  onAuthenticated,
  theme,
  onToggleTheme,
}: {
  onAuthenticated: (token: string) => void;
  theme: Theme;
  onToggleTheme: () => void;
}) {
  const [step, setStep] = useState<"request" | "verify">("request");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [deliveryMessage, setDeliveryMessage] = useState("");
  const online = useOnlineStatus();
  const action = useAction();
  async function submit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    await action.run(async () => {
      if (step === "request") {
        const response = await requestAdminOtp(email.trim());
        setDeliveryMessage(response.message);
        setStep("verify");
      } else {
        const response = await verifyAdminOtp(email.trim(), otp.trim());
        onAuthenticated(response.access_token);
      }
    });
  }
  return (
    <main className="auth admin-auth">
      <section className="auth-story admin-auth-story">
        <Brand />
        <div className="auth-story-copy">
          <p className="eyebrow">CONTROL DE PLATAFORMA</p>
          <h1>
            Cada comunidad.
            <br />
            Siempre en contexto.
          </h1>
          <p>
            Gestión centralizada, permisos separados y trazabilidad privada.
          </p>
        </div>
        <div className="admin-shield" aria-hidden="true">
          <Icon name="shield" />
        </div>
        <div className="auth-story-footer">
          <Icon name="shield" />
          <span>Acceso exclusivo de administración.</span>
          <span>ADMIN</span>
        </div>
      </section>
      <section className="auth-access">
        <ThemeToggle
          theme={theme}
          onToggle={onToggleTheme}
          className="auth-theme-toggle"
        />
        <div className="auth-mobile-brand">
          <Brand />
        </div>
        <div className="auth-form-wrap">
          <p className="eyebrow">ADMINISTRACIÓN FAIRCourt</p>
          <h2>{step === "request" ? "Acceso de plataforma" : "Verifica tu acceso"}</h2>
          <p className="muted">
            {step === "request"
              ? "Utiliza exclusivamente el correo autorizado como administrador."
              : `Introduce el código generado para ${email}.`}
          </p>
          {!online && <Notice kind="info">Necesitas conexión para entrar.</Notice>}
          <form className="auth-form" onSubmit={submit}>
            {step === "request" ? (
              <>
                <label htmlFor="admin-email">Correo administrativo</label>
                <input
                  id="admin-email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="email"
                  required
                  autoFocus
                />
              </>
            ) : (
              <>
                <Notice kind="info">{deliveryMessage}</Notice>
                <label htmlFor="admin-otp">Código de acceso</label>
                <input
                  id="admin-otp"
                  className="otp-input"
                  value={otp}
                  onChange={(event) => setOtp(event.target.value)}
                  autoComplete="one-time-code"
                  inputMode="numeric"
                  required
                  autoFocus
                />
                {import.meta.env.DEV && (
                  <p className="field-hint">Consulta el OTP ADMIN en Uvicorn.</p>
                )}
              </>
            )}
            <Feedback error={action.error} />
            <Button
              type="submit"
              className="full-width"
              disabled={!online || action.busy}
            >
              {action.busy
                ? "Comprobando…"
                : step === "request"
                  ? "Solicitar acceso administrativo"
                  : "Entrar al panel"}
              <Icon name="arrow" />
            </Button>
            {step === "verify" && (
              <Button
                variant="ghost"
                disabled={action.busy}
                onClick={() => {
                  setStep("request");
                  setOtp("");
                }}
              >
                Volver
              </Button>
            )}
          </form>
          <a className="admin-resident-link" href="/">
            Ir al acceso de residentes
          </a>
        </div>
      </section>
    </main>
  );
}

function AdminDashboard({
  onLogout,
  theme,
  onToggleTheme,
}: {
  onLogout: () => void;
  theme: Theme;
  onToggleTheme: () => void;
}) {
  const me = useResource(getAdminMe, "admin-me");
  const communities = useResource(getAdminCommunities, "admin-communities");
  const action = useAction();
  const [selected, setSelected] = useState<CommunitySummary>();
  const [policy, setPolicy] = useState<CommunityPolicy>();
  const [audit, setAudit] = useState<AdminAuditEntry[]>([]);

  async function choose(community: CommunitySummary) {
    await action.run(async () => {
      const selectedCommunity = await selectAdminCommunity(community.id);
      const [communityPolicy, privateAudit] = await Promise.all([
        getAdminCommunityPolicy(community.id),
        getAdminCommunityAudit(community.id),
      ]);
      setSelected(selectedCommunity);
      setPolicy(communityPolicy);
      setAudit(privateAudit);
      window.scrollTo({ top: 0 });
    });
  }

  return (
    <div className="admin-shell">
      <header className="admin-topbar">
        <Brand />
        <div className="admin-context" aria-live="polite">
          <span>Administrando</span>
          <strong>{selected?.name ?? "Selecciona una comunidad"}</strong>
        </div>
        <div className="admin-top-actions">
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
          <span className="admin-email">{me.data?.email}</span>
          <Button variant="ghost" onClick={onLogout}>
            <Icon name="logout" /> Cerrar sesión
          </Button>
        </div>
      </header>
      <main className="admin-main">
        <ResourceError error={me.error} retry={me.reload} />
        <ResourceError error={communities.error} retry={communities.reload} />
        <Feedback error={action.error} />
        {(me.loading || communities.loading) && !communities.data && <Loading />}
        {!selected ? (
          <section className="page-stack">
            <header className="page-heading">
              <div>
                <p className="eyebrow">ADMINISTRACIÓN DE PLATAFORMA</p>
                <h1>Elige la comunidad que vas a gestionar.</h1>
                <p className="muted">
                  Toda acción posterior quedará limitada y auditada dentro de
                  este contexto.
                </p>
              </div>
            </header>
            <div className="admin-community-grid">
              {communities.data?.map((community) => (
                <article className="panel admin-community-card" key={community.id}>
                  <div className="admin-card-heading">
                    <span className="admin-community-mark">
                      {community.name.slice(0, 2).toUpperCase()}
                    </span>
                    <Badge tone={community.is_active ? "green" : "red"}>
                      {community.is_active ? "Activa" : "Inactiva"}
                    </Badge>
                  </div>
                  <h2>{community.name}</h2>
                  <p className="muted">/{community.slug}</p>
                  <dl className="admin-card-stats">
                    <div><dt>Viviendas</dt><dd>{community.household_count}</dd></div>
                    <div><dt>Instalaciones</dt><dd>{community.facility_count}</dd></div>
                  </dl>
                  <Button
                    className="full-width"
                    disabled={action.busy}
                    onClick={() => choose(community)}
                  >
                    Administrar comunidad <Icon name="arrow" />
                  </Button>
                </article>
              ))}
            </div>
          </section>
        ) : (
          <CommunityWorkspace
            community={selected}
            policy={policy}
            audit={audit}
            onBack={() => {
              setSelected(undefined);
              setPolicy(undefined);
              setAudit([]);
            }}
          />
        )}
      </main>
    </div>
  );
}

function CommunityWorkspace({
  community,
  policy,
  audit,
  onBack,
}: {
  community: CommunitySummary;
  policy?: CommunityPolicy;
  audit: AdminAuditEntry[];
  onBack: () => void;
}) {
  const policyItems = policy
    ? [
        ["Ventana de reserva", `${policy.booking_window_days} días`],
        ["Reservas semanales", String(policy.max_active_reservations_per_week)],
        ["Cancelación", `${policy.cancellation_limit_hours} h antes`],
        ["Check-in", `${policy.checkin_window_minutes} min`],
        ["Strikes máximos", String(policy.max_strikes)],
        ["Suspensión", `${policy.suspension_days} días`],
        ["Listas de espera", String(policy.max_active_waitlists_per_week)],
        ["Horas punta", `${policy.prime_time_start_hour}:00–${policy.prime_time_end_hour}:00`],
        ["Cooldown", `${policy.cooldown_days} días`],
        ["Votaciones", policy.unlock_voting_enabled ? "Activadas" : "Desactivadas"],
      ]
    : [];
  return (
    <section className="page-stack">
      <header className="page-heading">
        <div>
          <p className="eyebrow">CONTEXTO ADMINISTRATIVO ACTIVO</p>
          <h1>{community.name}</h1>
          <p className="muted">
            {community.household_count} viviendas · {community.facility_count} instalaciones · {community.timezone}
          </p>
        </div>
        <Button variant="secondary" onClick={onBack}>
          Cambiar comunidad
        </Button>
      </header>
      <Notice kind="info">
        Todas las operaciones de esta pantalla pertenecen exclusivamente a <strong>{community.name}</strong>.
      </Notice>
      <section className="panel">
        <div className="section-heading">
          <h2>Política efectiva</h2>
          <Icon name="shield" />
        </div>
        <div className="admin-policy-grid">
          {policyItems.map(([label, value]) => (
            <div key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </section>
      <section className="panel">
        <div className="section-heading">
          <h2>Auditoría administrativa privada</h2>
          <span className="section-count">{audit.length}</span>
        </div>
        {audit.length ? (
          <div className="admin-audit-list">
            {audit.map((entry) => (
              <article key={entry.id}>
                <Icon name="history" />
                <div>
                  <strong>{entry.event}</strong>
                  <time dateTime={entry.created_at}>
                    {new Date(entry.created_at).toLocaleString("es-ES")}
                  </time>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="muted">Todavía no hay acciones administrativas registradas.</p>
        )}
      </section>
    </section>
  );
}
