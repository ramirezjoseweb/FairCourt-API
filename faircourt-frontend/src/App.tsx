import { useState } from "react";
import { requestOtp, verifyOtp } from "./api/auth";
import { Dashboard } from "./components/Dashboard";
import {
  Brand,
  Button,
  CourtArt,
  Feedback,
  Icon,
  Notice,
  ThemeToggle,
} from "./components/ui";
import { useAction } from "./hooks/useAction";
import { useOnlineStatus } from "./hooks/useOnlineStatus";
import { useTheme } from "./hooks/useTheme";
import { retryConnection } from "./utils/networkStatus";
import { getCommunitySlug } from "./utils/community";
import { clearCommunityCache } from "./utils/offlineCache";
import { AdminApp } from "./components/AdminApp";

export default function App() {
  const { theme, toggleTheme } = useTheme();
  if (window.location.pathname.startsWith("/admin")) {
    return <AdminApp theme={theme} onToggleTheme={toggleTheme} />;
  }
  return <ResidentApp theme={theme} onToggleTheme={toggleTheme} />;
}

function ResidentApp({
  theme,
  onToggleTheme,
}: {
  theme: "light" | "dark";
  onToggleTheme: () => void;
}) {
  const [token, setToken] = useState(() =>
    localStorage.getItem("faircourt_token"),
  );
  const [houseCode, setHouseCode] = useState("");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState<"request" | "verify">("request");
  const isOnline = useOnlineStatus();
  const action = useAction();
  const [deliveryMessage, setDeliveryMessage] = useState("");
  const communitySlug = getCommunitySlug();
  function logout() {
    clearCommunityCache();
    localStorage.removeItem("faircourt_token");
    setToken(null);
    setStep("request");
    setOtp("");
    setDeliveryMessage("");
  }
  if (token)
    return (
      <Dashboard onLogout={logout} theme={theme} onToggleTheme={onToggleTheme} />
    );
  async function submit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    await action.run(async () => {
      if (step === "request") {
        const response = await requestOtp({
          community_slug: communitySlug,
          house_code: houseCode.trim(),
          email: email.trim(),
        });
        setDeliveryMessage(response.message);
        setStep("verify");
      } else {
        const response = await verifyOtp({
          community_slug: communitySlug,
          email: email.trim(),
          otp: otp.trim(),
        });
        localStorage.setItem("faircourt_token", response.access_token);
        setToken(response.access_token);
      }
    });
  }
  return (
    <main className="auth">
      <section className="auth-story">
        <Brand />
        <div className="auth-story-copy">
          <p className="eyebrow">TU COMUNIDAD. TUS ESPACIOS.</p>
          <h1>
            Más juego.
            <br />
            Mejor comunidad.
          </h1>
          <p>
            Todos tus espacios compartidos.
            <br />
            Las mismas oportunidades para todos.
          </p>
        </div>
        <CourtArt />
        <div className="auth-story-footer">
          <Icon name="shield" />
          <span>Reservas justas. De principio a fin.</span>
          <span>01 / 01</span>
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
          <div className="auth-step">
            <span className="step-active">
              01 <span>Tu vivienda</span>
            </span>
            <i />
            <span className={step === "verify" ? "step-active" : ""}>
              02 <span>Verificación</span>
            </span>
          </div>
          <p className="eyebrow">BIENVENIDO A FAIRCourt</p>
          <h2>
            {step === "request"
              ? "Tu próxima partida empieza aquí."
              : "Ya casi estás dentro."}
          </h2>
          <p className="muted">
            {step === "request"
              ? "Accede con tu vivienda y disfruta de las instalaciones de tu comunidad."
              : `Introduce el código de acceso generado para ${email}.`}
          </p>
          {!isOnline && (
            <Notice kind="info">
              Necesitas conexión para iniciar sesión.{" "}
              {navigator.onLine && (
                <Button variant="ghost" onClick={retryConnection}>
                  Reintentar conexión
                </Button>
              )}
            </Notice>
          )}
          <form onSubmit={submit} className="auth-form">
            {step === "request" ? (
              <>
                <label htmlFor="house-code">Código de vivienda</label>
                <input
                  id="house-code"
                  value={houseCode}
                  onChange={(e) => setHouseCode(e.target.value)}
                  placeholder="Por ejemplo, A1"
                  autoComplete="username"
                  required
                  autoFocus
                />
                <label htmlFor="email">Correo electrónico</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="tu@correo.es"
                  autoComplete="email"
                  required
                />
                <p className="field-hint">
                  Utiliza el correo asociado a tu vivienda.
                </p>
              </>
            ) : (
              <>
                <Notice kind="info">{deliveryMessage}</Notice>
                <label htmlFor="otp">Código de acceso</label>
                <input
                  id="otp"
                  className="otp-input"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  placeholder="Introduce tu código"
                  autoComplete="one-time-code"
                  inputMode="numeric"
                  required
                  autoFocus
                />
                {import.meta.env.DEV && (
                  <p className="field-hint">
                    Entorno de desarrollo: consulta el OTP en la terminal de
                    Uvicorn.
                  </p>
                )}
              </>
            )}
            <Feedback error={action.error} />
            <Button
              type="submit"
              disabled={action.busy || !isOnline}
              className="full-width"
            >
              {action.busy
                ? "Un momento…"
                : step === "request"
                  ? "Solicitar código de acceso"
                  : "Entrar en FairCourt"}
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
                Volver a mis datos
              </Button>
            )}
          </form>
          <div className="auth-security">
            <Icon name="shield" />
            <span>Acceso seguro, sin contraseñas.</span>
          </div>
        </div>
        <footer className="auth-footer">
          FairCourt <span>El juego limpio empieza antes de jugar.</span>
        </footer>
      </section>
    </main>
  );
}
