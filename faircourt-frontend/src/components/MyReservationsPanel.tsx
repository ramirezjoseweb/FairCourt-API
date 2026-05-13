import { useEffect, useState } from "react";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import {
    cancelReservation,
    getMyReservations,
    getCheckinQr,
    type Reservation,
    type CheckinQrResponse,
} from "../api/reservations";

type MyReservationsPanelProps = {
    /**
     * Valor externo que fuerza la recarga del panel cuando cambia.
     */
    refreshKey?: number;

    /**
     * Callback opcional que se ejecuta cuando una acción modifica datos globales:
     * cancelación de reserva, check-in, etc.
     */
    onChanged?: () => void;
};

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

/**
 * Traduce el estado interno de una reserva a una etiqueta visible para el usuario.
 *
 * @param status Estado persistido o calculado de la reserva.
 */
function getStatusLabel(status: string) {
    const labels: Record<string, string> = {
        ACTIVE: "Activa",
        CANCELLED: "Cancelada",
        NO_SHOW: "No-show",
        FINISHED: "Finalizada",
    };

    return labels[status] || status;
}

/**
 * Devuelve clases visuales según el estado de la reserva.
 *
 * @param status Estado persistido o calculado de la reserva.
 */
function getStatusClasses(status: string) {
    if (status === "ACTIVE") {
        return "bg-green-50 text-green-700";
    }

    if (status === "CANCELLED") {
        return "bg-slate-100 text-slate-600";
    }

    if (status === "NO_SHOW") {
        return "bg-red-50 text-red-700";
    }

    if (status === "FINISHED") {
        return "bg-blue-50 text-blue-700";
    }

    return "bg-slate-100 text-slate-600";
}

/**
 * Panel de reservas de la vivienda autenticada.
 *
 * Permite:
 * - consultar reservas propias,
 * - visualizar su estado,
 * - cancelar reservas activas.
 */
export function MyReservationsPanel({
    refreshKey = 0,
    onChanged,
}: MyReservationsPanelProps) {
    const isOnline = useOnlineStatus();
    const [reservations, setReservations] = useState<Reservation[]>([]);
    const [loading, setLoading] = useState(false);
    const [actionLoading, setActionLoading] = useState<number | null>(null);
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [checkinData, setCheckinData] = useState<CheckinQrResponse | null>(null);
    const [checkinLoading, setCheckinLoading] = useState<number | null>(null);

    /**
     * Carga las reservas de la vivienda autenticada desde el backend.
     */
    async function loadReservations() {
        setLoading(true);
        setError(null);
        setMessage(null);

        try {
            const data = await getMyReservations();
            setReservations(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error cargando reservas.");
        } finally {
            setLoading(false);
        }
    }

    /**
     * Cancela una reserva y refresca la lista tras completar la operación.
     *
     * @param reservation Reserva seleccionada para cancelar.
     */
    async function handleCancel(reservation: Reservation) {
        // Si no hay conexión, no se puede realizar la acción.
        if (!isOnline) {
            setError("Cancelar una reserva requiere conexión.");
            return;
        }

        const confirmed = window.confirm(
            `¿Seguro que quieres cancelar la reserva del ${formatDateTime(
                reservation.start_at
            )}?`
        );

        if (!confirmed) {
            return;
        }

        setActionLoading(reservation.id);
        setError(null);
        setMessage(null);

        try {
            await cancelReservation(reservation.id);
            setMessage("Reserva cancelada correctamente.");
            await loadReservations();
            onChanged?.();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error cancelando reserva.");
        } finally {
            setActionLoading(null);
        }
    }

    /**
 * Solicita al backend la URL de check-in para una reserva activa.
 *
 * @param reservation Reserva sobre la que se solicita el check-in.
 */
    async function handleGetCheckin(reservation: Reservation) {
        // Si no hay conexión, no se puede realizar la acción.
        if (!isOnline) {
            setError("El check-in requiere conexión.");
            return;
        }
        setCheckinLoading(reservation.id);
        setError(null);
        setMessage(null);
        setCheckinData(null);

        try {
            const data = await getCheckinQr(reservation.id);
            setCheckinData(data);
            setMessage("URL de check-in generada correctamente.");
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Error generando URL de check-in."
            );
        } finally {
            setCheckinLoading(null);
        }
    }

    useEffect(() => {
        loadReservations();
    }, [refreshKey]);

    return (
        <section className="rounded-2xl bg-white p-6 shadow">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900">Mis reservas</h2>
                    <p className="mt-1 text-sm text-slate-600">
                        Consulta y gestiona las reservas asociadas a tu vivienda.
                    </p>
                </div>

                <button
                    onClick={loadReservations}
                    disabled={loading || !isOnline}
                    className="rounded-xl border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                    {!isOnline ? "Sin conexión" : loading ? "Actualizando..." : "Actualizar"}
                </button>
            </div>

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

            {!isOnline && (
                <p className="mt-4 rounded-xl bg-amber-50 p-3 text-sm text-amber-800">
                    Estás sin conexión. Puedes consultar tus últimas reservas guardadas, pero
                    cancelar o hacer check-in requiere conexión.
                </p>
            )}

            {checkinData && (
                <div className="mt-4 rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm font-semibold text-slate-700">
                        Check-in generado para reserva #{checkinData.reservation_id}
                    </p>

                    <p className="mt-2 text-xs text-slate-500">
                        Expira: {formatDateTime(checkinData.expires_at)}
                    </p>

                    <p className="mt-3 break-all rounded-xl bg-white p-3 text-xs text-slate-600">
                        {checkinData.checkin_url}
                    </p>

                    <div className="mt-3 flex flex-wrap gap-2">
                        <a
                            href={checkinData.checkin_url}
                            target="_blank"
                            rel="noreferrer"
                            className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
                        >
                            Abrir check-in
                        </a>

                        <button
                            onClick={() => navigator.clipboard.writeText(checkinData.checkin_url)}
                            className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                        >
                            Copiar URL
                        </button>
                    </div>
                </div>
            )}

            <div className="mt-6 space-y-3">
                {!loading && reservations.length === 0 && (
                    <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
                        Todavía no tienes reservas registradas.
                    </p>
                )}

                {reservations.map((reservation) => {
                    const visibleStatus = reservation.real_status || reservation.status;
                    const isActive = visibleStatus === "ACTIVE";
                    const isCancelling = actionLoading === reservation.id;

                    return (
                        <article
                            key={reservation.id}
                            className="flex flex-col gap-4 rounded-2xl border border-slate-200 p-5 sm:flex-row sm:items-center sm:justify-between"
                        >
                            <div>
                                <p className="text-lg font-bold text-slate-900">
                                    {formatDateTime(reservation.start_at)}
                                </p>

                                <p className="mt-1 text-sm text-slate-500">
                                    Hasta {formatDateTime(reservation.end_at)}
                                </p>

                                <div className="mt-3 flex flex-wrap gap-2">
                                    <span
                                        className={`rounded-full px-3 py-1 text-xs font-semibold ${getStatusClasses(
                                            visibleStatus
                                        )}`}
                                    >
                                        {getStatusLabel(visibleStatus)}
                                    </span>

                                    {reservation.status !== visibleStatus && (
                                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">
                                            BD: {reservation.status}
                                        </span>
                                    )}
                                </div>
                            </div>

                            <div className="flex flex-wrap gap-2">
                                <button
                                    onClick={() => handleGetCheckin(reservation)}
                                    disabled={!isOnline || !isActive || checkinLoading === reservation.id}
                                    className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
                                >
                                    {checkinLoading === reservation.id ? "Generando..." : "Check-in"}
                                </button>

                                <button
                                    onClick={() => handleCancel(reservation)}
                                    disabled={!isOnline || !isActive || isCancelling}
                                    className="rounded-xl bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-40"
                                >
                                    {isCancelling ? "Cancelando..." : "Cancelar"}
                                </button>
                            </div>
                        </article>
                    );
                })}
            </div>
        </section>
    );
}