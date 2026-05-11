import { apiRequest } from "./client";
import { loadFromCache, saveToCache } from "../utils/offlineCache";

/**
 * Payload para crear una propuesta de desbloqueo excepcional.
 */
export type CreateUnlockProposalPayload = {
    reason: string;
};

/**
 * Payload para votar una propuesta de desbloqueo.
 */
export type CastUnlockVotePayload = {
    vote: "YES" | "NO";
};

/**
 * Representa una propuesta de desbloqueo excepcional.
 */
export type UnlockProposal = {
    id: number;
    target_household_id: number;
    created_by_user_id: number;
    reason: string;
    status: string;
    created_at: string;
    closes_at: string;
    resolved_at: string | null;
};

/**
 * Representa un voto emitido sobre una propuesta de desbloqueo.
 */
export type UnlockVote = {
    id: number;
    proposal_id: number;
    voter_household_id: number;
    vote: string;
    created_at: string;
};

/**
 * Crea una propuesta de desbloqueo para la vivienda autenticada.
 *
 * El backend solo permitirá crearla si la vivienda está suspendida.
 */
export async function createUnlockProposal(
    payload: CreateUnlockProposalPayload
) {
    return apiRequest<UnlockProposal>("/unlock/proposal", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

/**
 * Obtiene las propuestas de desbloqueo existentes.
 *
 * Si hay conexión, guarda la respuesta en caché.
 * Si no hay conexión, muestra la última versión almacenada.
 */
export async function getUnlockProposals() {
    const cacheKey = "faircourt_cache_unlock_proposals";

    try {
        const data = await apiRequest<UnlockProposal[]>("/unlock/proposals");
        saveToCache(cacheKey, data);
        return data;
    } catch (error) {
        const cached = loadFromCache<UnlockProposal[]>(cacheKey);

        if (cached) {
            return cached;
        }

        throw error;
    }
}

/**
 * Emite un voto sobre una propuesta.
 *
 * @param proposalId Identificador de la propuesta.
 * @param payload Valor del voto: YES o NO.
 */
export async function castUnlockVote(
    proposalId: number,
    payload: CastUnlockVotePayload
) {
    return apiRequest<UnlockVote>(`/unlock/proposal/${proposalId}/vote`, {
        method: "POST",
        body: JSON.stringify(payload),
    });
}