import { useEffect, useState } from "react";
import { getMyAuditLog, type AuditLogEntry } from "../api/audit";

type AuditPanelProps = {
    /**
     * Valor externo que fuerza la recarga del panel cuando cambia.
     */
    refreshKey?: number;
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
 * Traduce el nombre técnico de un evento de auditoría
 * a una etiqueta más clara para el usuario.
 *
 * @param event Nombre interno del evento.
 */
function getEventLabel(event: string) {
    const labels: Record<string, string> = {
        OTP_REQUESTED: "OTP solicitado",
        OTP_VERIFIED: "OTP verificado",

        RESERVATION_CREATED: "Reserva creada",
        RESERVATION_CANCELLED: "Reserva cancelada",
        RESERVATION_NO_SHOW: "Reserva marcada como no-show",

        WAITLIST_JOINED: "Entrada en lista de espera",
        WAITLIST_LEFT: "Salida de lista de espera",
        WAITLIST_PROMOTED: "Promoción desde waitlist",
        WAITLIST_DROPPED: "Waitlist descartada",

        CHECKIN_COMPLETED: "Check-in realizado",

        STRIKE_ADDED: "Strike añadido",
        HOUSEHOLD_SUSPENDED: "Vivienda suspendida",

        UNLOCK_VOTE_CREATED: "Propuesta de desbloqueo creada",
        UNLOCK_VOTE_CAST: "Voto de desbloqueo registrado",
        UNLOCK_APPROVED: "Desbloqueo aprobado",
        UNLOCK_REJECTED: "Desbloqueo rechazado",
    };

    return labels[event] || event;
}

/**
 * Devuelve clases visuales según el tipo de evento.
 *
 * @param event Nombre interno del evento.
 */
function getEventClasses(event: string) {
    if (
        event === "RESERVATION_CREATED" ||
        event === "CHECKIN_COMPLETED" ||
        event === "WAITLIST_PROMOTED" ||
        event === "UNLOCK_APPROVED"
    ) {
        return "bg-green-50 text-green-700";
    }

    if (
        event === "RESERVATION_CANCELLED" ||
        event === "WAITLIST_LEFT" ||
        event === "WAITLIST_DROPPED"
    ) {
        return "bg-slate-100 text-slate-600";
    }

    if (
        event === "RESERVATION_NO_SHOW" ||
        event === "STRIKE_ADDED" ||
        event === "HOUSEHOLD_SUSPENDED" ||
        event === "UNLOCK_REJECTED"
    ) {
        return "bg-red-50 text-red-700";
    }

    if (
        event === "WAITLIST_JOINED" ||
        event === "UNLOCK_VOTE_CREATED" ||
        event === "UNLOCK_VOTE_CAST"
    ) {
        return "bg-purple-50 text-purple-700";
    }

    return "bg-blue-50 text-blue-700";
}

/**
 * Intenta parsear el campo metadata_json.
 *
 * El backend guarda los metadatos como string JSON para mantener
 * flexibilidad en los eventos de auditoría.
 *
 * @param metadataJson Cadena JSON almacenada en la auditoría.
 */
function parseMetadata(metadataJson: string | null): Record<string, unknown> {
    if (!metadataJson) {
        return {};
    }

    try {
        const parsed = JSON.parse(metadataJson);

        if (parsed && typeof parsed === "object") {
            return parsed as Record<string, unknown>;
        }

        return {};
    } catch {
        return {};
    }
}

/**
 * Formatea un valor de metadata para mostrarlo en pantalla.
 *
 * @param value Valor recibido dentro del objeto metadata.
 */
function formatMetadataValue(value: unknown) {
    if (value === null || value === undefined) {
        return "—";
    }

    if (typeof value === "string") {
        return value;
    }

    if (typeof value === "number" || typeof value === "boolean") {
        return String(value);
    }

    return JSON.stringify(value);
}

/**
 * Panel de auditoría visible.
 *
 * Permite consultar los eventos registrados para la vivienda autenticada,
 * aportando trazabilidad sobre las acciones realizadas en el sistema.
 */
export function AuditPanel({ refreshKey = 0 }: AuditPanelProps) {
    const [entries, setEntries] = useState<AuditLogEntry[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    /**
     * Carga el registro de auditoría de la vivienda autenticada.
     */
    async function loadAuditLog() {
        setLoading(true);
        setError(null);

        try {
            const data = await getMyAuditLog();
            setEntries(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error cargando auditoría.");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadAuditLog();
    }, [refreshKey]);

    return (
        <section className="rounded-2xl bg-white p-6 shadow">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900">Auditoría</h2>
                    <p className="mt-1 text-sm text-slate-600">
                        Registro visible de eventos asociados a tu vivienda.
                    </p>
                </div>

                <button
                    onClick={loadAuditLog}
                    disabled={loading}
                    className="rounded-xl border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                    {loading ? "Actualizando..." : "Actualizar"}
                </button>
            </div>

            {error && (
                <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">
                    {error}
                </p>
            )}

            <div className="mt-6 space-y-3">
                {!loading && entries.length === 0 && (
                    <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
                        Todavía no hay eventos de auditoría para esta vivienda.
                    </p>
                )}

                {entries.map((entry) => {
                    const metadata = parseMetadata(entry.metadata_json);
                    const metadataEntries = Object.entries(metadata);

                    return (
                        <article
                            key={entry.id}
                            className="rounded-2xl border border-slate-200 p-5"
                        >
                            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                                <div>
                                    <div className="flex flex-wrap items-center gap-2">
                                        <span
                                            className={`rounded-full px-3 py-1 text-xs font-semibold ${getEventClasses(
                                                entry.event
                                            )}`}
                                        >
                                            {getEventLabel(entry.event)}
                                        </span>

                                        {entry.reservation_id && (
                                            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                                                Reserva #{entry.reservation_id}
                                            </span>
                                        )}
                                    </div>

                                    <p className="mt-3 text-sm text-slate-500">
                                        Evento técnico:{" "}
                                        <span className="font-mono text-slate-700">
                                            {entry.event}
                                        </span>
                                    </p>

                                    <p className="mt-2 text-xs text-slate-500">
                                        {formatDateTime(entry.created_at)}
                                    </p>
                                </div>

                                <div className="text-xs text-slate-500">
                                    ID evento #{entry.id}
                                </div>
                            </div>

                            {metadataEntries.length > 0 && (
                                <div className="mt-4 rounded-xl bg-slate-50 p-4">
                                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                                        Metadatos
                                    </p>

                                    <dl className="mt-3 grid gap-2 sm:grid-cols-2">
                                        {metadataEntries.map(([key, value]) => (
                                            <div key={key}>
                                                <dt className="text-xs font-medium text-slate-500">
                                                    {key}
                                                </dt>
                                                <dd className="mt-1 break-all text-sm text-slate-800">
                                                    {formatMetadataValue(value)}
                                                </dd>
                                            </div>
                                        ))}
                                    </dl>
                                </div>
                            )}
                        </article>
                    );
                })}
            </div>
        </section>
    );
}