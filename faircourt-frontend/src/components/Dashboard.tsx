import { useEffect, useState } from "react";
import { getMe, type MeResponse } from "../api/me";
import { AppLayout, type AppView } from "./AppLayout";
import { DashboardHome } from "./DashboardHome";
import { MyReservationsPanel } from "./MyReservationsPanel";
import { NotificationsPanel } from "./NotificationsPanel";
import { SlotsPanel } from "./SlotsPanel";

type DashboardProps = {
    token: string;
    onLogout: () => void;
};

/**
 * Componente principal del área autenticada.
 *
 * Se encarga de:
 * - cargar los datos de la vivienda autenticada,
 * - controlar la vista activa,
 * - renderizar cada sección dentro del layout común.
 */
export function Dashboard({ token, onLogout }: DashboardProps) {
    const [me, setMe] = useState<MeResponse | null>(null);
    const [activeView, setActiveView] = useState<AppView>("home");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    /**
     * Carga la información del usuario/vivienda autenticada desde el backend.
     */
    async function loadMe() {
        setLoading(true);
        setError(null);

        try {
            const data = await getMe();
            setMe(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error cargando usuario.");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadMe();
    }, []);

    /**
     * Renderiza la vista activa seleccionada en la navegación.
     */
    function renderActiveView() {
        if (!me) {
            return null;
        }

        if (activeView === "home") {
            return <DashboardHome me={me} />;
        }

        if (activeView === "slots") {
            return <SlotsPanel />;
        }

        if (activeView === "reservations") {
            return <MyReservationsPanel />;
        }

        if (activeView === "notifications") {
            return <NotificationsPanel />;
        }

        if (activeView === "audit") {
            return (
                <section className="rounded-2xl bg-white p-6 shadow">
                    <h2 className="text-2xl font-bold text-slate-900">Auditoría</h2>
                    <p className="mt-2 text-slate-600">
                        Próximamente mostraremos aquí el registro de eventos de la vivienda.
                    </p>
                </section>
            );
        }

        if (activeView === "unlock") {
            return (
                <section className="rounded-2xl bg-white p-6 shadow">
                    <h2 className="text-2xl font-bold text-slate-900">Desbloqueos</h2>
                    <p className="mt-2 text-slate-600">
                        Próximamente podrás crear y votar propuestas de desbloqueo
                        excepcional.
                    </p>
                </section>
            );
        }

        return null;
    }

    if (loading) {
        return (
            <main className="min-h-screen bg-slate-100 p-6">
                <section className="mx-auto max-w-3xl rounded-2xl bg-white p-8 shadow">
                    <p className="text-slate-600">Cargando datos...</p>
                </section>
            </main>
        );
    }

    if (error) {
        return (
            <main className="min-h-screen bg-slate-100 p-6">
                <section className="mx-auto max-w-3xl rounded-2xl bg-red-50 p-8 text-red-700 shadow">
                    {error}
                    <button
                        onClick={onLogout}
                        className="mt-4 block rounded-xl bg-slate-900 px-4 py-2 text-white"
                    >
                        Cerrar sesión
                    </button>
                </section>
            </main>
        );
    }

    return (
        <AppLayout
            activeView={activeView}
            onChangeView={setActiveView}
            onLogout={onLogout}
        >
            {renderActiveView()}

            {activeView === "home" && (
                <section className="mt-6 rounded-2xl bg-white p-6 shadow">
                    <p className="text-sm font-medium text-slate-500">
                        Token JWT guardado
                    </p>
                    <p className="mt-2 break-all text-xs text-slate-500">{token}</p>
                </section>
            )}
        </AppLayout>
    );
}