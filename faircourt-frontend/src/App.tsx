import { useState } from "react";
import { requestOtp, verifyOtp } from "./api/auth";
import { Dashboard } from "./components/Dashboard"; // Importamos el componente Dashboard. 

// Componente principal de la aplicación.
function App() {
  // Estados para manejar el flujo de la aplicación.
  const [houseCode, setHouseCode] = useState("");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  // Estado que controla el paso actual del flujo de autenticación.
  const [step, setStep] = useState<"request" | "verify" | "done">("request");
  // Estado que almacena el token JWT.
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("faircourt_token")
  );
  // Estados para manejar el estado de carga, mensajes y errores.
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Función para solicitar un código OTP.
  async function handleRequestOtp(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    // Realiza la petición a la API para solicitar el código OTP.
    try { // Si la petición es exitosa, muestra el mensaje y cambia al paso de verificación.
      const response = await requestOtp({
        house_code: houseCode.trim(),
        email: email.trim(),
      });

      setMessage(response.message);
      setStep("verify");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error solicitando OTP");
    } finally {
      setLoading(false);
    }
  }

  // Función para verificar el código OTP y obtener el token.
  async function handleVerifyOtp(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    // Realiza la petición a la API para verificar el código OTP.
    try {
      // Si la petición es exitosa, guarda el token, muestra el mensaje y cambia al paso final.
      const response = await verifyOtp({
        email: email.trim(),
        otp: otp.trim(),
      });
      // Guarda el token JWT en el localStorage.
      localStorage.setItem("faircourt_token", response.access_token);
      setToken(response.access_token);
      setMessage("Sesión iniciada correctamente.");
      setStep("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error verificando OTP");
    } finally {
      setLoading(false);
    }
  }

  // Función para cerrar sesión.
  function handleLogout() {
    localStorage.removeItem("faircourt_token");
    setToken(null);
    setStep("request");
    setOtp("");
    setMessage(null);
    setError(null);
  }

  // Renderizado condicional basado en el estado del flujo.
  // Si hay token y estamos en el paso final, muestra el contenido de la sesión iniciada.
  if (token) {
    return <Dashboard token={token} onLogout={handleLogout} />; // Si existe token, muestra el dashboard.
  }
  // Si no hay token o no estamos en el paso final, muestra el formulario de inicio de sesión.
  return (
    <main className="min-h-screen bg-slate-100 p-6">
      <section className="mx-auto max-w-md rounded-2xl bg-white p-8 shadow">
        <h1 className="text-3xl font-bold text-slate-900">FairCourt</h1>
        <p className="mt-2 text-slate-600">
          Acceso mediante vivienda y código OTP.
        </p>
        {/* Formulario para solicitar el código OTP. */}
        {step === "request" && (
          <form onSubmit={handleRequestOtp} className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Código de vivienda
              </label>
              <input
                value={houseCode}
                onChange={(e) => setHouseCode(e.target.value)}
                placeholder="A1"
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-slate-900"
              />
            </div>
            {/* Campo de entrada para el email. */}
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Email
              </label>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="a1@example.com"
                type="email"
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-slate-900"
              />
            </div>
            {/* Botón para solicitar el código OTP. */}
            <button
              disabled={loading}
              className="w-full rounded-xl bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
            >
              {loading ? "Enviando..." : "Solicitar OTP"}
            </button>
          </form>
        )}
        {/* Formulario para verificar el código OTP. */}
        {step === "verify" && (
          <form onSubmit={handleVerifyOtp} className="mt-6 space-y-4">
            {/* Mensaje informativo sobre el código OTP. */}
            <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
              Se ha generado un OTP para <strong>{email}</strong>.
              En modo desarrollo, míralo en la terminal de Uvicorn.
            </div>
            {/* Campo de entrada para el código OTP. */}
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Código OTP
              </label>
              <input
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="123456"
                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-slate-900"
              />
            </div>
            {/* Botón para verificar el código OTP. */}
            <button
              disabled={loading}
              className="w-full rounded-xl bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
            >
              {loading ? "Verificando..." : "Verificar OTP"}
            </button>
            {/* Botón para volver al paso anterior. */}
            <button
              type="button"
              onClick={() => setStep("request")}
              className="w-full rounded-xl border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-50"
            >
              Volver
            </button>
          </form>
        )}
        {/* Mensaje de éxito si existe */}
        {message && (
          <p className="mt-4 rounded-xl bg-green-50 p-3 text-sm text-green-700">
            {message}
          </p>
        )}

        {error && (
          <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}
      </section>
    </main>
  );
}

export default App;