import { useState } from "react";
import {
  createAdminHousehold,
  createAdminFacility,
  getAdminCommunities,
  getAdminCommunityAudit,
  getAdminCommunityPolicy,
  getAdminFacilities,
  getAdminHouseholds,
  getAdminMe,
  importAdminHouseholdCsv,
  previewAdminHouseholdCsv,
  requestAdminOtp,
  selectAdminCommunity,
  updateAdminBasicPolicy,
  updateAdminFacility,
  updateAdminHousehold,
  updateAdminHouseholdAccess,
  verifyAdminOtp,
} from "../api/admin";
import type {
  AdminAuditEntry,
  AdminFacility,
  AdminFacilityInput,
  AdminHousehold,
  AdminHouseholdAccessInput,
  AdminHouseholdCsvImport,
  AdminHouseholdCsvInput,
  AdminHouseholdCsvPreview,
  AdminHouseholdUpdateInput,
  BasicPolicyInput,
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
  Dialog,
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
  const [facilities, setFacilities] = useState<AdminFacility[]>([]);
  const [households, setHouseholds] = useState<AdminHousehold[]>([]);

  async function choose(community: CommunitySummary) {
    await action.run(async () => {
      const selectedCommunity = await selectAdminCommunity(community.id);
      const [communityPolicy, privateAudit, communityFacilities, communityHouseholds] =
        await Promise.all([
          getAdminCommunityPolicy(community.id),
          getAdminCommunityAudit(community.id),
          getAdminFacilities(community.id),
          getAdminHouseholds(community.id),
        ]);
      setSelected(selectedCommunity);
      setPolicy(communityPolicy);
      setAudit(privateAudit);
      setFacilities(communityFacilities);
      setHouseholds(communityHouseholds);
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
            facilities={facilities}
            households={households}
            onBack={() => {
              setSelected(undefined);
              setPolicy(undefined);
              setAudit([]);
              setFacilities([]);
              setHouseholds([]);
              communities.reload();
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
  facilities: initialFacilities,
  households: initialHouseholds,
  onBack,
}: {
  community: CommunitySummary;
  policy?: CommunityPolicy;
  audit: AdminAuditEntry[];
  facilities: AdminFacility[];
  households: AdminHousehold[];
  onBack: () => void;
}) {
  const action = useAction();
  const [facilities, setFacilities] = useState(initialFacilities);
  const [households, setHouseholds] = useState(initialHouseholds);
  const [householdCount, setHouseholdCount] = useState(community.household_count);
  const [householdSearch, setHouseholdSearch] = useState("");
  const [householdForm, setHouseholdForm] = useState<
    AdminHousehold | "new" | null
  >(null);
  const [accessHousehold, setAccessHousehold] = useState<AdminHousehold | null>(
    null,
  );
  const [csvImportOpen, setCsvImportOpen] = useState(false);
  const [auditItems, setAuditItems] = useState(audit);
  const [policyValue, setPolicyValue] = useState(policy);
  const [policyFormOpen, setPolicyFormOpen] = useState(false);
  const [facilityForm, setFacilityForm] = useState<AdminFacility | "new" | null>(
    null,
  );
  const policyItems = policyValue
    ? [
        ["Ventana de reserva", `${policyValue.booking_window_days} días`],
        ["Reservas diarias por instalación", String(policyValue.max_active_reservations_per_day)],
        ["Reservas semanales por instalación", String(policyValue.max_active_reservations_per_week)],
        ["Cancelación", `${policyValue.cancellation_limit_hours} h antes`],
        ["Check-in", `${policyValue.checkin_window_minutes} min`],
        ["Strikes máximos", String(policyValue.max_strikes)],
        ["Suspensión", `${policyValue.suspension_days} días`],
        ["Listas de espera", String(policyValue.max_active_waitlists_per_week)],
        ["Horas punta", `${policyValue.prime_time_start_hour}:00–${policyValue.prime_time_end_hour}:00`],
        ["Cooldown", `${policyValue.cooldown_days} días`],
        ["Votaciones", policyValue.unlock_voting_enabled ? "Activadas" : "Desactivadas"],
      ]
    : [];
  const householdQuery = householdSearch.trim().toLocaleLowerCase("es");
  const filteredHouseholds = households.filter((household) =>
    [household.code, household.resident_email ?? ""].some((value) =>
      value.toLocaleLowerCase("es").includes(householdQuery),
    ),
  );
  const visibleHouseholds = filteredHouseholds.slice(0, 50);

  async function saveHousehold(payload: AdminHouseholdUpdateInput) {
    const editing = householdForm !== "new" ? householdForm : undefined;
    const success = await action.run(
      async () => {
        const saved = editing
          ? await updateAdminHousehold(
              community.id,
              editing.id,
              payload,
            )
          : await createAdminHousehold(community.id, { code: payload.code });
        setHouseholds((current) =>
          [...current.filter((item) => item.id !== saved.id), saved].sort(
            (left, right) =>
              left.code.localeCompare(right.code, "es", { numeric: true }),
          ),
        );
        if (!editing) setHouseholdCount((current) => current + 1);
        setAuditItems(await getAdminCommunityAudit(community.id));
      },
      editing ? "La vivienda se ha actualizado." : "La vivienda se ha creado.",
    );
    if (success) setHouseholdForm(null);
  }

  async function saveHouseholdAccess(payload: AdminHouseholdAccessInput) {
    if (!accessHousehold) return;
    const success = await action.run(async () => {
      const saved = await updateAdminHouseholdAccess(
        community.id,
        accessHousehold.id,
        payload,
      );
      setHouseholds((current) =>
        current.map((item) => (item.id === saved.id ? saved : item)),
      );
      setAuditItems(await getAdminCommunityAudit(community.id));
    }, "El acceso de la vivienda se ha actualizado.");
    if (success) setAccessHousehold(null);
  }

  async function acceptCsvImport(result: AdminHouseholdCsvImport) {
    setHouseholds((current) =>
      [...current, ...result.households].sort((left, right) =>
        left.code.localeCompare(right.code, "es", { numeric: true }),
      ),
    );
    setHouseholdCount((current) => current + result.created_count);
    setAuditItems(await getAdminCommunityAudit(community.id));
    setCsvImportOpen(false);
  }

  async function saveFacility(payload: AdminFacilityInput) {
    const editing = facilityForm !== "new" ? facilityForm : undefined;
    const success = await action.run(
      async () => {
        const saved = editing
          ? await updateAdminFacility(community.id, editing.id, payload)
          : await createAdminFacility(community.id, payload);
        setFacilities((current) =>
          [...current.filter((item) => item.id !== saved.id), saved].sort(
            (left, right) =>
              left.priority - right.priority ||
              left.name.localeCompare(right.name, "es"),
          ),
        );
        setAuditItems(await getAdminCommunityAudit(community.id));
      },
      editing
        ? "La instalación se ha actualizado."
        : "La instalación se ha creado.",
    );
    if (success) setFacilityForm(null);
  }

  async function saveBasicPolicy(payload: BasicPolicyInput) {
    const success = await action.run(async () => {
      const saved = await updateAdminBasicPolicy(community.id, payload);
      setPolicyValue(saved);
      setAuditItems(await getAdminCommunityAudit(community.id));
    }, "Las reglas básicas se han actualizado.");
    if (success) setPolicyFormOpen(false);
  }

  return (
    <section className="page-stack">
      <header className="page-heading">
        <div>
          <p className="eyebrow">CONTEXTO ADMINISTRATIVO ACTIVO</p>
          <h1>{community.name}</h1>
          <p className="muted">
            {householdCount} viviendas · {facilities.length} instalaciones · {community.timezone}
          </p>
        </div>
        <Button variant="secondary" onClick={onBack}>
          Cambiar comunidad
        </Button>
      </header>
      <Notice kind="info">
        Todas las operaciones de esta pantalla pertenecen exclusivamente a <strong>{community.name}</strong>.
      </Notice>
      <Feedback error={action.error} message={action.message} />
      <section className="panel admin-households-panel" aria-labelledby="admin-households-title">
        <div className="section-heading admin-section-heading">
          <div>
            <p className="eyebrow">RESIDENTES Y ACCESO</p>
            <h2 id="admin-households-title">Viviendas</h2>
          </div>
          <div className="admin-section-actions">
            <Button
              variant="secondary"
              disabled={action.busy}
              onClick={() => setCsvImportOpen(true)}
            >
              Importar CSV
            </Button>
            <Button disabled={action.busy} onClick={() => setHouseholdForm("new")}>
              <Icon name="plus" /> Nueva vivienda
            </Button>
          </div>
        </div>
        <p className="muted small admin-household-explanation">
          Cada código pertenece solo a esta comunidad. El residente vinculará su correo en el primer acceso.
        </p>
        {households.length ? (
          <>
            <label className="admin-household-search">
              <span>Buscar vivienda o correo vinculado</span>
              <input
                type="search"
                value={householdSearch}
                placeholder="Ej. GRP001 o vecino@correo.es"
                onChange={(event) => setHouseholdSearch(event.target.value)}
              />
            </label>
            <div className="admin-household-results" aria-live="polite">
              <span>
                {filteredHouseholds.length} de {households.length} viviendas
              </span>
              {filteredHouseholds.length > visibleHouseholds.length && (
                <span>Mostrando las primeras {visibleHouseholds.length}</span>
              )}
            </div>
            {visibleHouseholds.length ? (
              <div className="admin-household-list">
                {visibleHouseholds.map((household) => {
                  const titleId = `admin-household-${household.id}`;
                  return (
                    <article key={household.id} aria-labelledby={titleId}>
                      <span className="admin-household-icon">
                        <Icon name="home" />
                      </span>
                      <div className="admin-household-main">
                        <strong id={titleId}>{household.code}</strong>
                        <span className="muted small">
                          {household.resident_email ?? "Sin cuenta vinculada"}
                        </span>
                      </div>
                      <div className="admin-household-status">
                        <Badge tone={household.is_active ? "green" : "red"}>
                          {household.is_active ? "Activa" : "Inactiva"}
                        </Badge>
                        <span className="muted small">
                          {household.resident_email ? "Cuenta vinculada" : "Pendiente de acceso"}
                        </span>
                        <Button
                          variant="secondary"
                          disabled={action.busy}
                          aria-label={`Editar ${household.code}`}
                          onClick={() => setHouseholdForm(household)}
                        >
                          Editar
                        </Button>
                        <Button
                          variant="secondary"
                          disabled={action.busy}
                          aria-label={`Gestionar acceso de ${household.code}`}
                          onClick={() => setAccessHousehold(household)}
                        >
                          Gestionar acceso
                        </Button>
                      </div>
                    </article>
                  );
                })}
              </div>
            ) : (
              <p className="muted admin-household-no-results">
                No hay viviendas que coincidan con la búsqueda.
              </p>
            )}
          </>
        ) : (
          <div className="admin-empty-state">
            <Icon name="home" />
            <h3>Todavía no hay viviendas.</h3>
            <p className="muted">Crea la primera para habilitar el acceso de sus residentes.</p>
          </div>
        )}
      </section>
      <section className="panel admin-facilities-panel">
        <div className="section-heading admin-section-heading">
          <div>
            <p className="eyebrow">CATÁLOGO DE LA COMUNIDAD</p>
            <h2>Instalaciones</h2>
          </div>
          <Button disabled={action.busy} onClick={() => setFacilityForm("new")}>
            <Icon name="plus" /> Nueva instalación
          </Button>
        </div>
        {facilities.length ? (
          <div className="admin-facility-grid">
            {facilities.map((facility) => {
              const titleId = `admin-facility-${facility.id}`;
              return (
                <article
                  className={`admin-facility-card ${facility.is_active ? "" : "is-inactive"}`}
                  key={facility.id}
                  aria-labelledby={titleId}
                >
                  <div className="admin-facility-heading">
                    <span className="admin-facility-icon">
                      <Icon name="court" />
                    </span>
                    <div>
                      <h3 id={titleId}>{facility.name}</h3>
                      <span className="muted small">/{facility.slug}</span>
                    </div>
                    <Badge tone={facility.is_active ? "green" : "red"}>
                      {facility.is_active ? "Activa" : "Inactiva"}
                    </Badge>
                  </div>
                  {facility.description && <p>{facility.description}</p>}
                  <dl className="admin-facility-details">
                    <div><dt>Categoría</dt><dd>{facility.category}</dd></div>
                    <div><dt>Horario</dt><dd>{facility.opening_hour}:00–{facility.closing_hour}:00</dd></div>
                    <div><dt>Duración</dt><dd>{facility.slot_duration_minutes} min</dd></div>
                    <div><dt>Orden</dt><dd>{facility.priority}</dd></div>
                  </dl>
                  <div className="admin-facility-footer">
                    <Badge tone={facility.is_reservable ? "green" : "amber"}>
                      {facility.is_reservable ? "Reservable" : "No reservable"}
                    </Badge>
                    <Button
                      variant="secondary"
                      disabled={action.busy}
                      onClick={() => setFacilityForm(facility)}
                    >
                      Editar
                    </Button>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="admin-empty-state">
            <Icon name="court" />
            <h3>Todavía no hay instalaciones.</h3>
            <p className="muted">Crea la primera para empezar a configurar sus reservas.</p>
          </div>
        )}
      </section>
      <section className="panel" aria-labelledby="admin-policy-title">
        <div className="section-heading admin-section-heading">
          <div>
            <p className="eyebrow">REGLAS DE RESERVA</p>
            <h2 id="admin-policy-title">Política efectiva</h2>
          </div>
          <Button
            variant="secondary"
            disabled={action.busy || !policyValue}
            onClick={() => setPolicyFormOpen(true)}
          >
            Editar reglas básicas
          </Button>
        </div>
        <p className="muted small admin-policy-explanation">
          Los límites diario y semanal se aplican a cada vivienda por separado en cada instalación.
        </p>
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
          <span className="section-count">{auditItems.length}</span>
        </div>
        {auditItems.length ? (
          <div className="admin-audit-list">
            {auditItems.map((entry) => (
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
      {facilityForm && (
        <FacilityFormDialog
          facility={facilityForm === "new" ? undefined : facilityForm}
          busy={action.busy}
          error={action.error}
          onClose={() => setFacilityForm(null)}
          onSave={saveFacility}
        />
      )}
      {householdForm && (
        <HouseholdFormDialog
          household={householdForm === "new" ? undefined : householdForm}
          busy={action.busy}
          error={action.error}
          onClose={() => setHouseholdForm(null)}
          onSave={saveHousehold}
        />
      )}
      {accessHousehold && (
        <HouseholdAccessDialog
          household={accessHousehold}
          busy={action.busy}
          error={action.error}
          onClose={() => setAccessHousehold(null)}
          onSave={saveHouseholdAccess}
        />
      )}
      {csvImportOpen && (
        <HouseholdCsvImportDialog
          communityId={community.id}
          onClose={() => setCsvImportOpen(false)}
          onImported={acceptCsvImport}
        />
      )}
      {policyFormOpen && policyValue && (
        <BasicPolicyFormDialog
          policy={policyValue}
          busy={action.busy}
          error={action.error}
          onClose={() => setPolicyFormOpen(false)}
          onSave={saveBasicPolicy}
        />
      )}
    </section>
  );
}

function downloadHouseholdCsvTemplate() {
  const content =
    "\ufeffcodigo_vivienda;correo;activa\r\n" +
    "VIVIENDA-001;vecino@example.com;si\r\n" +
    "VIVIENDA-002;;si\r\n";
  const url = URL.createObjectURL(
    new Blob([content], { type: "text/csv;charset=utf-8" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = "plantilla-viviendas.csv";
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function HouseholdCsvImportDialog({
  communityId,
  onClose,
  onImported,
}: {
  communityId: number;
  onClose: () => void;
  onImported: (result: AdminHouseholdCsvImport) => Promise<void>;
}) {
  const action = useAction();
  const [file, setFile] = useState<AdminHouseholdCsvInput>();
  const [fileError, setFileError] = useState("");
  const [preview, setPreview] = useState<AdminHouseholdCsvPreview>();

  async function selectFile(event: React.ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0];
    setPreview(undefined);
    setFileError("");
    if (!selected) {
      setFile(undefined);
      return;
    }
    if (selected.size > 1_000_000) {
      setFile(undefined);
      setFileError("El archivo no puede superar 1 MB.");
      return;
    }
    try {
      setFile({ file_name: selected.name, csv_text: await selected.text() });
    } catch {
      setFile(undefined);
      setFileError("No se ha podido leer el archivo.");
    }
  }

  async function review() {
    if (!file) return;
    await action.run(async () => {
      setPreview(await previewAdminHouseholdCsv(communityId, file));
    });
  }

  async function confirm() {
    if (!file || !preview?.can_import) return;
    await action.run(async () => {
      const result = await importAdminHouseholdCsv(communityId, file);
      await onImported(result);
    });
  }

  const visibleRows = preview?.rows.slice(0, 100) ?? [];
  return (
    <Dialog title="Importar viviendas desde CSV" onClose={onClose}>
      <div className="admin-csv-form">
        <p className="muted">
          Crea viviendas nuevas sin modificar las que ya existen. El correo y el
          estado son opcionales.
        </p>
        <Notice kind="info">
          Columnas: <strong>codigo_vivienda</strong>, <strong>correo</strong> y{" "}
          <strong>activa</strong>. Se aceptan archivos separados por punto y coma
          o coma.
        </Notice>
        <Button variant="secondary" onClick={downloadHouseholdCsvTemplate}>
          Descargar plantilla CSV
        </Button>
        <label className="admin-form-field">
          <span>Archivo CSV</span>
          <input type="file" accept=".csv,text/csv" onChange={selectFile} />
          <small className="field-hint">Máximo 2.000 viviendas y 1 MB.</small>
        </label>
        <Feedback error={fileError || action.error} />
        {file && !preview && (
          <Button disabled={action.busy} onClick={review}>
            {action.busy ? "Revisando…" : "Revisar archivo"}
          </Button>
        )}
        {preview && (
          <>
            <div className="admin-csv-summary" aria-live="polite">
              <div><strong>{preview.new_count}</strong><span>Nuevas</span></div>
              <div><strong>{preview.existing_count}</strong><span>Ya existen</span></div>
              <div><strong>{preview.error_count}</strong><span>Con errores</span></div>
            </div>
            {preview.error_count > 0 && (
              <Notice kind="error">
                Corrige todas las filas con errores y vuelve a seleccionar el archivo.
                No se ha creado ninguna vivienda.
              </Notice>
            )}
            <div className="admin-csv-table-wrap">
              <table className="admin-csv-table">
                <thead>
                  <tr><th>Línea</th><th>Vivienda</th><th>Correo</th><th>Resultado</th></tr>
                </thead>
                <tbody>
                  {visibleRows.map((row) => (
                    <tr key={row.line}>
                      <td>{row.line}</td>
                      <td>{row.code || "—"}</td>
                      <td>{row.email ?? "—"}</td>
                      <td>
                        <Badge
                          tone={
                            row.status === "new"
                              ? "green"
                              : row.status === "error"
                                ? "red"
                                : "amber"
                          }
                        >
                          {row.status === "new"
                            ? "Nueva"
                            : row.status === "existing"
                              ? "Ya existe"
                              : "Error"}
                        </Badge>
                        {row.message && <span className="admin-csv-message">{row.message}</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {preview.total_rows > visibleRows.length && (
              <p className="field-hint">
                Se muestran las primeras {visibleRows.length} de {preview.total_rows} filas.
              </p>
            )}
          </>
        )}
        <div className="dialog-actions">
          <Button variant="secondary" disabled={action.busy} onClick={onClose}>
            Cancelar
          </Button>
          <Button
            disabled={action.busy || !preview?.can_import}
            onClick={confirm}
          >
            {action.busy && preview
              ? "Importando…"
              : `Importar ${preview?.new_count ?? 0} viviendas`}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

function HouseholdAccessDialog({
  household,
  busy,
  error,
  onClose,
  onSave,
}: {
  household: AdminHousehold;
  busy: boolean;
  error?: string;
  onClose: () => void;
  onSave: (payload: AdminHouseholdAccessInput) => Promise<void>;
}) {
  const [email, setEmail] = useState("");
  const normalizedEmail = email.trim().toLocaleLowerCase("es");
  const currentEmail = household.resident_email?.toLocaleLowerCase("es") ?? "";
  const unchanged = Boolean(currentEmail) && normalizedEmail === currentEmail;

  return (
    <Dialog title={`Gestionar acceso de ${household.code}`} onClose={onClose}>
      <form
        className="admin-household-form"
        onSubmit={(event) => {
          event.preventDefault();
          if (!unchanged) void onSave({ email: normalizedEmail });
        }}
      >
        <div className="admin-access-current">
          <span>Correo vinculado actualmente</span>
          <strong>{household.resident_email ?? "Sin cuenta vinculada"}</strong>
        </div>
        <label className="admin-form-field">
          <span>
            {household.resident_email
              ? "Nuevo correo de acceso"
              : "Correo de acceso"}
          </span>
          <input
            type="email"
            value={email}
            maxLength={254}
            required
            autoFocus
            autoComplete="off"
            placeholder="residente@correo.es"
            onChange={(event) => setEmail(event.target.value)}
          />
          {unchanged && (
            <small className="field-hint">
              Introduce un correo diferente al actual.
            </small>
          )}
        </label>
        {!household.is_active && (
          <Notice kind="info">
            La vivienda seguirá sin poder entrar hasta que también la actives.
          </Notice>
        )}
        <Notice kind="info">
          El acceso anterior y sus OTP pendientes dejarán de funcionar. Las reservas, strikes e historial seguirán perteneciendo a la vivienda.
        </Notice>
        <Feedback error={error} />
        <div className="dialog-actions">
          <Button variant="secondary" disabled={busy} onClick={onClose}>
            Cancelar
          </Button>
          <Button
            type="submit"
            disabled={busy || !normalizedEmail || unchanged}
          >
            {busy
              ? "Guardando…"
              : household.resident_email
                ? "Cambiar correo"
                : "Asignar acceso"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

function HouseholdFormDialog({
  household,
  busy,
  error,
  onClose,
  onSave,
}: {
  household?: AdminHousehold;
  busy: boolean;
  error?: string;
  onClose: () => void;
  onSave: (payload: AdminHouseholdUpdateInput) => Promise<void>;
}) {
  const [code, setCode] = useState(household?.code ?? "");
  const [isActive, setIsActive] = useState(household?.is_active ?? true);

  return (
    <Dialog
      title={household ? `Editar ${household.code}` : "Nueva vivienda"}
      onClose={onClose}
    >
      <form
        className="admin-household-form"
        onSubmit={(event) => {
          event.preventDefault();
          void onSave({ code: code.trim(), is_active: isActive });
        }}
      >
        <label className="admin-form-field">
          <span>Código de vivienda</span>
          <input
            value={code}
            maxLength={50}
            required
            autoFocus
            placeholder="Ej. GRP001 o Bloque 18 3ºB"
            aria-describedby="household-code-help"
            onChange={(event) => setCode(event.target.value)}
          />
          <small id="household-code-help" className="field-hint">
            Debe ser único dentro de {"esta comunidad"}. Puede repetirse en otra comunidad.
          </small>
        </label>
        {household ? (
          <>
            <div className="admin-form-checks">
              <label>
                <input
                  type="checkbox"
                  checked={isActive}
                  onChange={(event) => setIsActive(event.target.checked)}
                />
                <span>Vivienda activa</span>
              </label>
            </div>
            <Notice kind="info">
              Al desactivarla se bloquean el acceso y las reservas nuevas. Sus reservas existentes no se cancelan.
            </Notice>
          </>
        ) : (
          <Notice kind="info">
            No necesitas indicar un correo. La cuenta quedará vinculada cuando el residente solicite su primer OTP.
          </Notice>
        )}
        <Feedback error={error} />
        <div className="dialog-actions">
          <Button variant="secondary" disabled={busy} onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={busy || !code.trim()}>
            {busy
              ? "Guardando…"
              : household
                ? "Guardar cambios"
                : "Crear vivienda"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

function BasicPolicyFormDialog({
  policy,
  busy,
  error,
  onClose,
  onSave,
}: {
  policy: CommunityPolicy;
  busy: boolean;
  error?: string;
  onClose: () => void;
  onSave: (payload: BasicPolicyInput) => Promise<void>;
}) {
  const [form, setForm] = useState<BasicPolicyInput>({
    booking_window_days: policy.booking_window_days,
    max_active_reservations_per_day: policy.max_active_reservations_per_day,
    max_active_reservations_per_week: policy.max_active_reservations_per_week,
    cancellation_limit_hours: policy.cancellation_limit_hours,
  });

  function setField<K extends keyof BasicPolicyInput>(
    field: K,
    value: BasicPolicyInput[K],
  ) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  return (
    <Dialog title="Editar reglas básicas" onClose={onClose}>
      <form
        className="admin-facility-form admin-policy-form"
        onSubmit={(event) => {
          event.preventDefault();
          void onSave(form);
        }}
      >
        <label className="admin-form-field">
          <span>Días de antelación</span>
          <input
            type="number"
            min="0"
            max="365"
            value={form.booking_window_days}
            required
            autoFocus
            onChange={(event) => setField("booking_window_days", Number(event.target.value))}
          />
        </label>
        <label className="admin-form-field">
          <span>Reservas diarias por instalación</span>
          <input
            type="number"
            min="0"
            max="50"
            value={form.max_active_reservations_per_day}
            required
            onChange={(event) =>
              setField("max_active_reservations_per_day", Number(event.target.value))
            }
          />
        </label>
        <label className="admin-form-field">
          <span>Reservas semanales por instalación</span>
          <input
            type="number"
            min="0"
            max="100"
            value={form.max_active_reservations_per_week}
            required
            onChange={(event) =>
              setField("max_active_reservations_per_week", Number(event.target.value))
            }
          />
        </label>
        <label className="admin-form-field">
          <span>Horas mínimas para cancelar</span>
          <input
            type="number"
            min="0"
            max="336"
            value={form.cancellation_limit_hours}
            required
            onChange={(event) =>
              setField("cancellation_limit_hours", Number(event.target.value))
            }
          />
        </label>
        <p className="field-hint admin-form-field-wide">
          Un límite igual a 0 bloquea nuevas reservas en ese periodo. Los cambios se aplican inmediatamente.
        </p>
        <Feedback error={error} />
        <div className="dialog-actions admin-form-field-wide">
          <Button variant="secondary" disabled={busy} onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={busy}>
            {busy ? "Guardando…" : "Guardar reglas"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

function facilitySlug(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function FacilityFormDialog({
  facility,
  busy,
  error,
  onClose,
  onSave,
}: {
  facility?: AdminFacility;
  busy: boolean;
  error?: string;
  onClose: () => void;
  onSave: (payload: AdminFacilityInput) => Promise<void>;
}) {
  const [slugTouched, setSlugTouched] = useState(Boolean(facility));
  const [form, setForm] = useState<AdminFacilityInput>(() => ({
    slug: facility?.slug ?? "",
    name: facility?.name ?? "",
    category: facility?.category ?? "Deporte",
    description: facility?.description ?? "",
    icon: facility?.icon ?? "court",
    priority: facility?.priority ?? 100,
    is_active: facility?.is_active ?? true,
    is_reservable: facility?.is_reservable ?? true,
    opening_hour: facility?.opening_hour ?? 9,
    closing_hour: facility?.closing_hour ?? 22,
    slot_duration_minutes: facility?.slot_duration_minutes ?? 60,
  }));
  const invalidSchedule = form.opening_hour >= form.closing_hour;

  function setField<K extends keyof AdminFacilityInput>(
    field: K,
    value: AdminFacilityInput[K],
  ) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  return (
    <Dialog
      title={facility ? `Editar ${facility.name}` : "Nueva instalación"}
      onClose={onClose}
    >
      <form
        className="admin-facility-form"
        onSubmit={(event) => {
          event.preventDefault();
          if (!invalidSchedule) void onSave(form);
        }}
      >
        <label className="admin-form-field admin-form-field-wide">
          <span>Nombre visible</span>
          <input
            value={form.name}
            maxLength={120}
            required
            autoFocus
            onChange={(event) => {
              const name = event.target.value;
              setForm((current) => ({
                ...current,
                name,
                slug: slugTouched ? current.slug : facilitySlug(name),
              }));
            }}
          />
        </label>
        <label className="admin-form-field admin-form-field-wide">
          <span>Código interno</span>
          <input
            value={form.slug}
            maxLength={80}
            pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
            required
            aria-describedby="facility-slug-help"
            onChange={(event) => {
              setSlugTouched(true);
              setField("slug", event.target.value.toLowerCase());
            }}
          />
          <small id="facility-slug-help" className="field-hint">
            Único dentro de esta comunidad. Usa letras, números y guiones.
          </small>
        </label>
        <label className="admin-form-field">
          <span>Categoría</span>
          <input
            value={form.category}
            maxLength={80}
            list="facility-categories"
            required
            onChange={(event) => setField("category", event.target.value)}
          />
          <datalist id="facility-categories">
            <option value="Deporte" />
            <option value="Encuentros" />
            <option value="Interior" />
            <option value="Bienestar" />
          </datalist>
        </label>
        <label className="admin-form-field">
          <span>Orden de aparición</span>
          <input
            type="number"
            min="0"
            max="9999"
            value={form.priority}
            required
            onChange={(event) => setField("priority", Number(event.target.value))}
          />
        </label>
        <label className="admin-form-field">
          <span>Hora de apertura</span>
          <input
            type="number"
            min="0"
            max="23"
            value={form.opening_hour}
            required
            onChange={(event) => setField("opening_hour", Number(event.target.value))}
          />
        </label>
        <label className="admin-form-field">
          <span>Hora de cierre</span>
          <input
            type="number"
            min="1"
            max="24"
            value={form.closing_hour}
            required
            onChange={(event) => setField("closing_hour", Number(event.target.value))}
          />
        </label>
        <label className="admin-form-field admin-form-field-wide">
          <span>Duración de cada reserva</span>
          <select
            value={form.slot_duration_minutes}
            onChange={(event) =>
              setField("slot_duration_minutes", Number(event.target.value))
            }
          >
            {[30, 45, 60, 90, 120].map((minutes) => (
              <option key={minutes} value={minutes}>{minutes} minutos</option>
            ))}
          </select>
        </label>
        <label className="admin-form-field admin-form-field-wide">
          <span>Descripción</span>
          <textarea
            value={form.description ?? ""}
            maxLength={500}
            onChange={(event) => setField("description", event.target.value || null)}
          />
        </label>
        <div className="admin-form-checks admin-form-field-wide">
          <label>
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(event) => setField("is_active", event.target.checked)}
            />
            <span>Instalación activa</span>
          </label>
          <label>
            <input
              type="checkbox"
              checked={form.is_reservable}
              onChange={(event) => setField("is_reservable", event.target.checked)}
            />
            <span>Admite reservas</span>
          </label>
        </div>
        {invalidSchedule && (
          <Notice kind="error">La hora de cierre debe ser posterior a la apertura.</Notice>
        )}
        <Feedback error={error} />
        <div className="dialog-actions admin-form-field-wide">
          <Button variant="secondary" disabled={busy} onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={busy || invalidSchedule}>
            {busy ? "Guardando…" : facility ? "Guardar cambios" : "Crear instalación"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
