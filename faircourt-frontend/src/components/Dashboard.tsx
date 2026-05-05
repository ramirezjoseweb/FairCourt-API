import { useEffect, useState } from "react";
import { getMe, type MeResponse } from "../api/me";

type DashboardProps = {
    token: string;
    onLogout: () => void;
};

// Función que muestra el dashboard del usuario autenticado.
export function Dashboard({ token, onLogout }: DashboardProps) {
    // Estados para almacenar los datos del usuario, el estado de carga y los errores.
    const [me, setMe] = useState<MeResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Función para cargar los datos del usuario.
    async function loadMe() {
        setLoading(true);
        setError(null);

        // Intenta obtener los datos del usuario.
        try {
            const data = await getMe();
            setMe(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error cargando usuario.");
        } finally {
            setLoading(false);
        }
    }
    // Effect que se ejecuta cuando el componente se monta.
    useEffect(() => {
        loadMe();
    }, []);

    // Renderizado del dashboard.
    return (
        <main className="min-h-screen bg-slate-100 p-6">
            <section className="mx-auto max-w-5xl space-y-6">
                <header className="rounded-2xl bg-white p-6 shadow">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-slate-900">FairCourt</h1>
                            <p className="mt-1 text-slate-600">
                                Panel principal de la vivienda autenticada.
                            </p>
                        </div>

                        <button
                            onClick={onLogout}
                            className="rounded-xl bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-700"
                        >
                            Cerrar sesión
                        </button>
                    </div>
                </header>

                {/* Si hay un estado de carga, muestra un mensaje. */}
                {loading && (
                    <div className="rounded-2xl bg-white p-6 shadow">
                        <p className="text-slate-600">Cargando datos...</p>
                    </div>
                )}
                {/* Si hay un error, muestra un mensaje. */}
                {error && (
                    <div className="rounded-2xl bg-red-50 p-6 text-red-700 shadow">
                        {error}
                    </div>
                )}
                {/* Si hay datos del usuario, muestra el dashboard. */}
                {me && (
                    <div className="grid gap-6 md:grid-cols-3">
                        {/* Tarjeta para mostrar el email del usuario. */}
                        <article className="rounded-2xl bg-white p-6 shadow">
                            <p className="text-sm font-medium text-slate-500">Email</p>
                            <p className="mt-2 text-xl font-bold text-slate-900">
                                {me.email}
                            </p>
                        </article>

                        {/* Tarjeta para mostrar el ID de la vivienda. */}
                        <article className="rounded-2xl bg-white p-6 shadow">
                            <p className="text-sm font-medium text-slate-500">Vivienda</p>
                            <p className="mt-2 text-xl font-bold text-slate-900">
                                ID {me.household_id}
                            </p>
                        </article>

                        {/* Tarjeta para mostrar el número de strikes. */}
                        <article className="rounded-2xl bg-white p-6 shadow">
                            <p className="text-sm font-medium text-slate-500">Strikes</p>
                            <p className="mt-2 text-xl font-bold text-slate-900">
                                {me.strikes ?? 0}
                            </p>
                        </article>

                        {/* Tarjeta para mostrar el estado de suspensión. */}
                        <article className="rounded-2xl bg-white p-6 shadow md:col-span-2">
                            <p className="text-sm font-medium text-slate-500">
                                Estado de suspensión
                            </p>
                            <p className="mt-2 text-lg font-semibold text-slate-900">
                                {me.suspended_until
                                    ? `Suspendida hasta ${new Date(
                                        me.suspended_until
                                    ).toLocaleString("es-ES")}`
                                    : "Sin suspensión activa"}
                            </p>
                        </article>

                        {/* Tarjeta para mostrar el número de waitlists activas. */}
                        <article className="rounded-2xl bg-white p-6 shadow">
                            <p className="text-sm font-medium text-slate-500">
                                Waitlists activas
                            </p>
                            <p className="mt-2 text-xl font-bold text-slate-900">
                                {me.active_waitlists_count ?? 0}
                            </p>
                        </article>
                    </div>
                )}

                {/* Sección para mostrar el token JWT. */}
                <section className="rounded-2xl bg-white p-6 shadow">
                    <p className="text-sm font-medium text-slate-500">
                        Token JWT guardado
                    </p>
                    <p className="mt-2 break-all text-xs text-slate-500">{token}</p>
                </section>
            </section>
        </main>
    );
}