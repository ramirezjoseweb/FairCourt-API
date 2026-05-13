import { useEffect, useState } from "react";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import {
    createReservation,
    getSlots,
    joinWaitlist,
    type Slot,
} from "../api/reservations";

type SlotsPanelProps = {
    /**
     * Callback opcional que se ejecuta cuando una acción modifica datos globales:
     * creación de reserva, entrada en waitlist, etc.
     */
    onChanged?: () => void;
};

// Función que convierte una fecha a formato string para input date.
function toInputDate(date: Date) {
    return date.toISOString().slice(0, 10);
}

// Función que formatea un string de fecha a hora.
function formatTime(value: string) {
    return new Date(value).toLocaleTimeString("es-ES", {
        hour: "2-digit",
        minute: "2-digit",
    });
}

// Función que formatea un string de fecha a fecha y hora.
function formatDateTime(value: string) {
    return new Date(value).toLocaleString("es-ES", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

// Componente que muestra el panel de slots.
export function SlotsPanel({ onChanged }: SlotsPanelProps) {
    // Estado para almacenar el día seleccionado, los slots, el estado de carga, el estado de acción, el mensaje y los errores.
    const isOnline = useOnlineStatus();
    const [day, setDay] = useState(toInputDate(new Date()));
    const [slots, setSlots] = useState<Slot[]>([]);
    const [loading, setLoading] = useState(false);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Función que carga los slots del día seleccionado.
    // Función que carga los slots del día seleccionado.
    async function loadSlots() {
        setLoading(true);
        setError(null);
        setMessage(null);

        // Intenta obtener los slots del día seleccionado.
        try {
            const data = await getSlots(day);
            setSlots(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error cargando slots.");
        } finally {
            setLoading(false);
        }
    }

    // Función que maneja la reserva de un slot.
    async function handleReserve(slot: Slot) {
        setActionLoading(slot.start_at);
        setError(null);
        setMessage(null);

        // Si no hay conexión, no se puede realizar la acción.
        if (!isOnline) {
            setError("Esta acción requiere conexión.");
            return;
        }

        // Intenta crear la reserva.
        try {
            await createReservation(slot.start_at);
            setMessage(`Reserva creada para ${formatDateTime(slot.start_at)}.`);
            await loadSlots();
            onChanged?.();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error creando reserva.");
        } finally {
            setActionLoading(null);
        }
    }

    // Función que maneja la reserva de un slot.
    async function handleJoinWaitlist(slot: Slot) {
        setActionLoading(slot.start_at);
        setError(null);
        setMessage(null);

        // Si no hay conexión, no se puede realizar la acción.
        if (!isOnline) {
            setError("Esta acción requiere conexión.");
            return;
        }

        // Intenta crear la reserva.
        try {
            await joinWaitlist(slot.start_at);
            setMessage(`Te has unido a la lista de espera para ${formatDateTime(slot.start_at)}.`);
            await loadSlots();
            onChanged?.();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error entrando en waitlist.");
        } finally {
            setActionLoading(null);
        }
    }

    // Función que se ejecuta al montar el componente para cargar los slots.
    useEffect(() => {
        loadSlots();
    }, []);

    // Renderizado del componente.
    return (
        <section className="rounded-2xl bg-white p-6 shadow">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900">Disponibilidad</h2>
                    <p className="mt-1 text-sm text-slate-600">
                        Consulta slots, reserva o apúntate a lista de espera.
                    </p>
                </div>

                <div className="flex gap-3">
                    <div>
                        <label className="block text-sm font-medium text-slate-700">
                            Día
                        </label>
                        <input
                            type="date"
                            value={day}
                            onChange={(e) => setDay(e.target.value)}
                            className="mt-1 rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-slate-900"
                        />
                    </div>

                    <button
                        onClick={loadSlots}
                        disabled={loading}
                        className="rounded-xl bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
                    >
                        {loading ? "Cargando..." : "Consultar"}
                    </button>
                </div>
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
                    Estás sin conexión. Puedes consultar los últimos slots guardados, pero reservar
                    o entrar en lista de espera requiere conexión.
                </p>
            )}

            <div className="mt-6 grid gap-4 md:grid-cols-2">
                {slots.map((slot) => {
                    const isBusy = actionLoading === slot.start_at;
                    // Renderizado de cada slot.
                    return (
                        <article
                            key={slot.start_at}
                            className="rounded-2xl border border-slate-200 p-5"
                        >
                            <div className="flex items-start justify-between gap-4">
                                <div>
                                    <p className="text-lg font-bold text-slate-900">
                                        {formatTime(slot.start_at)} - {formatTime(slot.end_at)}
                                    </p>

                                    <div className="mt-2 flex flex-wrap gap-2">
                                        <span
                                            className={`rounded-full px-3 py-1 text-xs font-semibold ${slot.status === "FREE"
                                                ? "bg-green-50 text-green-700"
                                                : "bg-amber-50 text-amber-700"
                                                }`}
                                        >
                                            {slot.status === "FREE" ? "Libre" : "Ocupado"}
                                        </span>

                                        {slot.is_mine && (
                                            <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                                                Tu reserva
                                            </span>
                                        )}

                                        {slot.in_waitlist && (
                                            <span className="rounded-full bg-purple-50 px-3 py-1 text-xs font-semibold text-purple-700">
                                                En waitlist
                                            </span>
                                        )}
                                    </div>

                                    <p className="mt-3 text-sm text-slate-500">
                                        Waitlist: {slot.waitlist_count}
                                    </p>
                                </div>

                                <div className="flex flex-col gap-2">
                                    <button
                                        onClick={() => handleReserve(slot)}
                                        disabled={!isOnline || !slot.can_book || isBusy}
                                        className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
                                    >
                                        Reservar
                                    </button>

                                    <button
                                        onClick={() => handleJoinWaitlist(slot)}
                                        disabled={!isOnline || !slot.can_join_waitlist || isBusy}
                                        className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                                    >
                                        Waitlist
                                    </button>
                                </div>
                            </div>
                            {/* Muestra el motivo por el que no se puede reservar el slot. */}
                            {slot.book_reason && !slot.can_book && (
                                <p className="mt-3 text-xs text-slate-400">
                                    Reserva bloqueada: {slot.book_reason}
                                </p>
                            )}
                            {/* Muestra el motivo por el que no se puede unirse a la lista de espera. */}
                            {slot.waitlist_reason && !slot.can_join_waitlist && (
                                <p className="mt-1 text-xs text-slate-400">
                                    Waitlist bloqueada: {slot.waitlist_reason}
                                </p>
                            )}
                        </article>
                    );
                })}
            </div>
        </section>
    );
}