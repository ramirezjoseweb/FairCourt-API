import { useEffect, useState } from "react";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import {
    castUnlockVote,
    createUnlockProposal,
    getUnlockProposals,
    type UnlockProposal,
} from "../api/unlock";
import type { MeResponse } from "../api/me";

type UnlockPanelProps = {
    me: MeResponse;
    refreshKey?: number;
    onRefreshMe?: () => void;
};

/**
 * Formatea una fecha ISO en formato legible para la interfaz.
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
 * Traduce el estado técnico de una propuesta a una etiqueta en español.
 *
 * @param status Estado interno de la propuesta.
 */
function getProposalStatusLabel(status: string) {
    const labels: Record<string, string> = {
        OPEN: "Abierta",
        APPROVED: "Aprobada",
        REJECTED: "Rechazada",
        EXPIRED: "Expirada",
    };

    return labels[status] || status;
}

/**
 * Devuelve clases visuales para el estado de una propuesta.
 *
 * @param status Estado interno de la propuesta.
 */
function getProposalStatusClasses(status: string) {
    if (status === "OPEN") {
        return "bg-blue-50 text-blue-700";
    }

    if (status === "APPROVED") {
        return "bg-green-50 text-green-700";
    }

    if (status === "REJECTED" || status === "EXPIRED") {
        return "bg-red-50 text-red-700";
    }

    return "bg-slate-100 text-slate-600";
}

/**
 * Panel de desbloqueos excepcionales.
 *
 * Permite:
 * - crear una propuesta si la vivienda está suspendida,
 * - consultar propuestas existentes,
 * - votar propuestas de otras viviendas.
 */
export function UnlockPanel({
    me,
    refreshKey = 0,
    onRefreshMe,
}: UnlockPanelProps) {
    const isOnline = useOnlineStatus();
    const [proposals, setProposals] = useState<UnlockProposal[]>([]);
    const [reason, setReason] = useState("");
    const [loading, setLoading] = useState(false);
    const [creating, setCreating] = useState(false);
    const [votingProposalId, setVotingProposalId] = useState<number | null>(null);
    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const isSuspended = Boolean(me.suspended_until);

    /**
     * Carga las propuestas de desbloqueo desde el backend.
     */
    async function loadProposals() {
        setLoading(true);
        setError(null);

        try {
            const data = await getUnlockProposals();
            setProposals(data);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Error cargando propuestas."
            );
        } finally {
            setLoading(false);
        }
    }

    /**
     * Crea una propuesta de desbloqueo para la vivienda autenticada.
     *
     * Solo tiene sentido si la vivienda está suspendida.
     */
    async function handleCreateProposal(event: React.FormEvent) {
        // Si no hay conexión, no se puede realizar la acción.
        if (!isOnline) {
            setError("Crear una propuesta requiere conexión.");
            return;
        }

        event.preventDefault();

        if (!reason.trim()) {
            setError("Debes indicar un motivo para solicitar el desbloqueo.");
            return;
        }

        setCreating(true);
        setError(null);
        setMessage(null);

        try {
            await createUnlockProposal({ reason: reason.trim() });
            setReason("");
            setMessage("Propuesta de desbloqueo creada correctamente.");
            await loadProposals();
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Error creando propuesta."
            );
        } finally {
            setCreating(false);
        }
    }

    /**
     * Emite un voto YES/NO sobre una propuesta.
     *
     * @param proposal Propuesta sobre la que se emite el voto.
     * @param vote Valor del voto.
     */
    async function handleVote(proposal: UnlockProposal, vote: "YES" | "NO") {
        // Si no hay conexión, no se puede realizar la acción.
        if (!isOnline) {
            setError("Votar una propuesta requiere conexión.");
            return;
        }

        setVotingProposalId(proposal.id);
        setError(null);
        setMessage(null);

        try {
            await castUnlockVote(proposal.id, { vote });
            setMessage(`Voto ${vote} registrado correctamente.`);
            await loadProposals();
            onRefreshMe?.();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Error registrando voto.");
        } finally {
            setVotingProposalId(null);
        }
    }

    useEffect(() => {
        loadProposals();
    }, [refreshKey]);

    return (
        <section className="space-y-6">
            <section className="rounded-2xl bg-white p-6 shadow">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                        <h2 className="text-2xl font-bold text-slate-900">
                            Desbloqueos excepcionales
                        </h2>
                        <p className="mt-1 text-sm text-slate-600">
                            Solicita o vota desbloqueos temporales sin administrador
                            permanente.
                        </p>
                    </div>

                    <button
                        onClick={loadProposals}
                        disabled={loading}
                        className="rounded-xl border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                    >
                        {loading ? "Actualizando..." : "Actualizar"}
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
                        Estás sin conexión. Puedes consultar las últimas propuestas guardadas, pero
                        crear propuestas o votar requiere conexión.
                    </p>
                )}
            </section>

            <section className="rounded-2xl bg-white p-6 shadow">
                <h3 className="text-xl font-bold text-slate-900">
                    Crear propuesta de desbloqueo
                </h3>

                {isSuspended ? (
                    <form onSubmit={handleCreateProposal} className="mt-4 space-y-4">
                        <div className="rounded-xl bg-red-50 p-4 text-sm text-red-700">
                            Tu vivienda está suspendida
                            {me.suspended_until
                                ? ` hasta ${formatDateTime(me.suspended_until)}`
                                : ""}
                            . Puedes solicitar un desbloqueo excepcional.
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700">
                                Motivo de la solicitud
                            </label>

                            <textarea
                                value={reason}
                                onChange={(event) => setReason(event.target.value)}
                                rows={4}
                                placeholder="Explica brevemente el motivo del desbloqueo excepcional..."
                                className="mt-1 w-full rounded-xl border border-slate-300 px-3 py-2 outline-none focus:border-slate-900"
                            />
                        </div>

                        <button
                            disabled={!isOnline || creating}
                            className="rounded-xl bg-slate-900 px-4 py-2 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
                        >
                            {creating ? "Creando..." : "Crear propuesta"}
                        </button>
                    </form>
                ) : (
                    <p className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
                        Tu vivienda no está suspendida actualmente, por lo que no necesita
                        solicitar desbloqueo.
                    </p>
                )}
            </section>

            <section className="rounded-2xl bg-white p-6 shadow">
                <h3 className="text-xl font-bold text-slate-900">
                    Propuestas existentes
                </h3>

                <div className="mt-6 space-y-3">
                    {!loading && proposals.length === 0 && (
                        <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
                            No hay propuestas de desbloqueo registradas.
                        </p>
                    )}

                    {proposals.map((proposal) => {
                        const isOwnHousehold =
                            proposal.target_household_id === me.household_id;
                        const isOpen = proposal.status === "OPEN";
                        const isVoting = votingProposalId === proposal.id;

                        return (
                            <article
                                key={proposal.id}
                                className="rounded-2xl border border-slate-200 p-5"
                            >
                                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                                    <div>
                                        <div className="flex flex-wrap items-center gap-2">
                                            <span
                                                className={`rounded-full px-3 py-1 text-xs font-semibold ${getProposalStatusClasses(
                                                    proposal.status
                                                )}`}
                                            >
                                                {getProposalStatusLabel(proposal.status)}
                                            </span>

                                            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                                                Vivienda #{proposal.target_household_id}
                                            </span>

                                            {isOwnHousehold && (
                                                <span className="rounded-full bg-purple-50 px-3 py-1 text-xs font-semibold text-purple-700">
                                                    Tu propuesta
                                                </span>
                                            )}
                                        </div>

                                        <p className="mt-3 text-sm font-medium text-slate-900">
                                            {proposal.reason}
                                        </p>

                                        <p className="mt-2 text-xs text-slate-500">
                                            Creada: {formatDateTime(proposal.created_at)}
                                        </p>

                                        <p className="mt-1 text-xs text-slate-500">
                                            Cierre: {formatDateTime(proposal.closes_at)}
                                        </p>

                                        {proposal.resolved_at && (
                                            <p className="mt-1 text-xs text-slate-500">
                                                Resuelta: {formatDateTime(proposal.resolved_at)}
                                            </p>
                                        )}
                                    </div>

                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleVote(proposal, "YES")}
                                            disabled={!isOnline || !isOpen || isOwnHousehold || isVoting}
                                            className="rounded-xl bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-500 disabled:cursor-not-allowed disabled:opacity-40"
                                        >
                                            Sí
                                        </button>

                                        <button
                                            onClick={() => handleVote(proposal, "NO")}
                                            disabled={!isOnline || !isOpen || isOwnHousehold || isVoting}
                                            className="rounded-xl bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-40"
                                        >
                                            No
                                        </button>
                                    </div>
                                </div>

                                {isOwnHousehold && isOpen && (
                                    <p className="mt-4 rounded-xl bg-slate-50 p-3 text-xs text-slate-600">
                                        La vivienda afectada no puede votar su propia propuesta.
                                    </p>
                                )}
                            </article>
                        );
                    })}
                </div>
            </section>
        </section>
    );
}