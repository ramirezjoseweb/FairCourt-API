import { apiRequest } from "./client";
import { loadFromCache, saveToCache } from "../utils/offlineCache";

/**
 * Representa un evento de auditoría generado por el backend.
 *
 * La auditoría registra eventos relevantes del sistema:
 * creación de reservas, cancelaciones, waitlist, no-shows,
 * suspensiones, desbloqueos, etc.
 */
export type AuditLogEntry = {
    id: number;
    event: string;
    household_id: number | null;
    user_id: number | null;
    reservation_id: number | null;
    metadata_json: string | null;
    created_at: string;
};

/**
 * Obtiene el registro de auditoría asociado a la vivienda autenticada.
 *
 * Si hay conexión, actualiza la caché.
 * Si no hay conexión, devuelve los últimos eventos guardados.
 */
export async function getMyAuditLog() {
    const cacheKey = "faircourt_cache_audit";

    try {
        const data = await apiRequest<AuditLogEntry[]>("/audit/me");
        saveToCache(cacheKey, data);
        return data;
    } catch (error) {
        const cached = loadFromCache<AuditLogEntry[]>(cacheKey);

        if (cached) {
            return cached;
        }

        throw error;
    }
}