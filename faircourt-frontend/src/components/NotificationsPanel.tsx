import { useEffect, useState } from "react";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import {
    getMyNotifications,
    markNotificationAsRead,
    type Notification,
} from "../api/notifications";

/**
 * Formatea una fecha ISO a formato legible en español.
 *
 * @param value Fecha/hora en formato ISO.
 */
function formatDateTime(value: string) {
    return new Date(value).toLocaleString("es-ES", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

type NotificationsPanelProps = {
    /**
     * Valor externo que fuerza la recarga del panel cuando cambia.
     */
    refreshKey?: number;
};

/**
 * Traduce el tipo interno de notificación a una etiqueta más legible.
 *
 * @param type Tipo técnico de notificación.
 */
function getNotificationTypeLabel(type: string) {
    const labels: Record<string, string> = {
        RESERVATION_CREATED: "Reserva creada",
        RESERVATION_CANCELLED: "Reserva cancelada",
        WAITLIST_JOINED: "Lista de espera",
        WAITLIST_PROMOTED: "Promoción waitlist",
        NO_SHOW: "No-show",
        HOUSEHOLD_SUSPENDED: "Suspensión",
    };

    return labels[type] || type;
}

/**
 * Devuelve clases visuales según el tipo de notificación.
 *
 * @param type Tipo técnico de notificación.
 */
function getNotificationTypeClasses(type: string) {
    if (type === "RESERVATION_CREATED" || type === "WAITLIST_PROMOTED") {
        return "bg-green-50 text-green-700";
    }

    if (type === "RESERVATION_CANCELLED") {
        return "bg-slate-100 text-slate-600";
    }

    if (type === "NO_SHOW" || type === "HOUSEHOLD_SUSPENDED") {
        return "bg-red-50 text-red-700";
    }

    if (type === "WAITLIST_JOINED") {
        return "bg-purple-50 text-purple-700";
    }

    return "bg-blue-50 text-blue-700";
}

/**
 * Panel de notificaciones internas.
 *
 * Permite:
 * - listar notificaciones de la vivienda autenticada,
 * - distinguir entre leídas y no leídas,
 * - marcar notificaciones como leídas.
 */
export function NotificationsPanel({
    refreshKey = 0,
}: NotificationsPanelProps) {
    const isOnline = useOnlineStatus();
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [loading, setLoading] = useState(false);
    const [actionLoading, setActionLoading] = useState<number | null>(null);
    const [error, setError] = useState<string | null>(null);

    /**
     * Carga las notificaciones desde el backend.
     */
    async function loadNotifications() {
        setLoading(true);
        setError(null);

        try {
            const data = await getMyNotifications();
            setNotifications(data);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Error cargando notificaciones."
            );
        } finally {
            setLoading(false);
        }
    }

    /**
     * Marca una notificación como leída y actualiza el estado local.
     *
     * @param notification Notificación seleccionada.
     */
    async function handleMarkAsRead(notification: Notification) {
        // Si no hay conexión, no se puede realizar la acción.
        if (!isOnline) {
            setError("Marcar una notificación como leída requiere conexión.");
            return;
        }

        setActionLoading(notification.id);
        setError(null);

        try {
            const updated = await markNotificationAsRead(notification.id);

            setNotifications((current) =>
                current.map((item) => (item.id === updated.id ? updated : item))
            );
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Error marcando notificación."
            );
        } finally {
            setActionLoading(null);
        }
    }

    useEffect(() => {
        loadNotifications();
    }, [refreshKey]);

    const unreadCount = notifications.filter((item) => !item.is_read).length;

    return (
        <section className="rounded-2xl bg-white p-6 shadow">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900">Notificaciones</h2>
                    <p className="mt-1 text-sm text-slate-600">
                        Avisos internos generados por reservas, waitlist y penalizaciones.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-700">
                        {unreadCount} sin leer
                    </span>

                    <button
                        onClick={loadNotifications}
                        disabled={loading}
                        className="rounded-xl border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                    >
                        {loading ? "Actualizando..." : "Actualizar"}
                    </button>
                </div>
            </div>

            {error && (
                <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">
                    {error}
                </p>
            )}

            {!isOnline && (
                <p className="mt-4 rounded-xl bg-amber-50 p-3 text-sm text-amber-800">
                    Estás sin conexión. Puedes consultar las últimas notificaciones guardadas,
                    pero marcarlas como leídas requiere conexión.
                </p>
            )}

            <div className="mt-6 space-y-3">
                {!loading && notifications.length === 0 && (
                    <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
                        Todavía no tienes notificaciones.
                    </p>
                )}

                {notifications.map((notification) => {
                    const isReading = actionLoading === notification.id;

                    return (
                        <article
                            key={notification.id}
                            className={`rounded-2xl border p-5 ${notification.is_read
                                ? "border-slate-200 bg-white"
                                : "border-slate-300 bg-slate-50"
                                }`}
                        >
                            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                                <div>
                                    <div className="flex flex-wrap items-center gap-2">
                                        <span
                                            className={`rounded-full px-3 py-1 text-xs font-semibold ${getNotificationTypeClasses(
                                                notification.type
                                            )}`}
                                        >
                                            {getNotificationTypeLabel(notification.type)}
                                        </span>

                                        {!notification.is_read && (
                                            <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                                                Nueva
                                            </span>
                                        )}
                                    </div>

                                    <p className="mt-3 text-sm font-medium text-slate-900">
                                        {notification.message}
                                    </p>

                                    <p className="mt-2 text-xs text-slate-500">
                                        {formatDateTime(notification.created_at)}
                                    </p>
                                </div>

                                <button
                                    onClick={() => handleMarkAsRead(notification)}
                                    disabled={!isOnline || notification.is_read || isReading}
                                    className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
                                >
                                    {notification.is_read
                                        ? "Leída"
                                        : isReading
                                            ? "Marcando..."
                                            : "Marcar leída"}
                                </button>
                            </div>
                        </article>
                    );
                })}
            </div>
        </section>
    );
}