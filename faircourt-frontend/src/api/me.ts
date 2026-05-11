import { apiRequest } from "./client";
import { loadFromCache, saveToCache } from "../utils/offlineCache";

const ME_CACHE_KEY = "faircourt_cache_me";

/**
 * Datos resumidos del usuario autenticado y de su vivienda.
 */
export type MeResponse = {
    id: number;
    email: string;
    household_id: number;
    household_code?: string | null;
    strikes?: number;
    suspended_until?: string | null;
    active_waitlists_count?: number;
};

/**
 * Obtiene los datos del usuario autenticado desde el backend.
 *
 * Si la petición funciona, actualiza la caché local.
 * Si falla por falta de conexión, intenta devolver la última versión cacheada.
 */
export async function getMe() {
    try {
        const data = await apiRequest<MeResponse>("/me");
        saveToCache(ME_CACHE_KEY, data);
        return data;
    } catch (error) {
        const cached = loadFromCache<MeResponse>(ME_CACHE_KEY);

        if (cached) {
            return cached;
        }

        throw error;
    }
}