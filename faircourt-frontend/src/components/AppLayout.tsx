import { useEffect, useState } from "react";
import { getMyNotifications } from "../api/notifications";
import { OfflineBanner } from "./OfflineBanner";
import { useOnlineStatus } from "../hooks/useOnlineStatus";

export type AppView =
    | "home"
    | "slots"
    | "reservations"
    | "notifications"
    | "audit"
    | "unlock";

type AppLayoutProps = {
    activeView: AppView;
    onChangeView: (view: AppView) => void;
    onLogout: () => void;
    children: React.ReactNode;
};

/**
 * Layout principal de la aplicación autenticada.
 *
 * Centraliza:
 * - la barra superior de navegación,
 * - el acceso a las distintas secciones,
 * - el contador de notificaciones no leídas,
 * - la acción de cierre de sesión.
 */
export function AppLayout({
    activeView,
    onChangeView,
    onLogout,
    children,
}: AppLayoutProps) {
    const isOnline = useOnlineStatus();
    const [unreadCount, setUnreadCount] = useState(0);

    /**
     * Carga el número de notificaciones pendientes de lectura.
     * Se usa en la barra superior para mostrar un contador visible.
     */
    async function loadUnreadNotifications() {
        try {
            const notifications = await getMyNotifications();
            const count = notifications.filter((item) => !item.is_read).length;
            setUnreadCount(count);
        } catch {
            setUnreadCount(0);
        }
    }

    useEffect(() => {
        loadUnreadNotifications();
    }, [activeView]);

    const navItems: { id: AppView; label: string }[] = [
        { id: "home", label: "Inicio" },
        { id: "slots", label: "Disponibilidad" },
        { id: "reservations", label: "Mis reservas" },
        { id: "audit", label: "Auditoría" },
        { id: "unlock", label: "Desbloqueos" },
    ];

    return (
        <main className="min-h-screen bg-slate-100">
            <OfflineBanner isOnline={isOnline} />
            <header className="sticky top-0 z-10 border-b border-slate-200 bg-white">
                <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-slate-900">FairCourt</h1>
                        <p className="text-sm text-slate-500">
                            Sistema justo de reservas comunitarias
                        </p>
                    </div>

                    <nav className="flex flex-wrap items-center gap-2">
                        {navItems.map((item) => (
                            <button
                                key={item.id}
                                onClick={() => onChangeView(item.id)}
                                className={`rounded-xl px-4 py-2 text-sm font-medium transition ${activeView === item.id
                                    ? "bg-slate-900 text-white"
                                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                                    }`}
                            >
                                {item.label}
                            </button>
                        ))}

                        <button
                            onClick={() => onChangeView("notifications")}
                            className={`relative rounded-xl px-4 py-2 text-sm font-medium transition ${activeView === "notifications"
                                ? "bg-slate-900 text-white"
                                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                                }`}
                        >
                            Notificaciones
                            {unreadCount > 0 && (
                                <span className="ml-2 rounded-full bg-red-600 px-2 py-0.5 text-xs font-bold text-white">
                                    {unreadCount}
                                </span>
                            )}
                        </button>

                        <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${isOnline
                                ? "bg-green-50 text-green-700"
                                : "bg-amber-50 text-amber-700"
                                }`}
                        >
                            {isOnline ? "Online" : "Offline"}
                        </span>

                        <button
                            onClick={onLogout}
                            className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                        >
                            Cerrar sesión
                        </button>
                    </nav>
                </div>
            </header>

            <section className="mx-auto max-w-7xl px-6 py-6">{children}</section>
        </main>
    );
}