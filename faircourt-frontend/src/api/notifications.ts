import { apiRequest } from "./client";
import { loadFromCache, saveToCache } from "../utils/offlineCache";

/**
 * Representa una notificación interna generada por el backend.
 *
 * Las notificaciones informan a la vivienda sobre eventos relevantes:
 * reservas, cancelaciones, waitlist, no-shows, suspensiones, etc.
 */
export type Notification = {
    id: number;
    user_id: number;
    household_id: number;
    type: string;
    message: string;
    is_read: boolean;
    created_at: string;
};

/**
 * Obtiene las notificaciones asociadas a la vivienda autenticada.
 *
 * En modo online actualiza la caché local.
 * En modo offline devuelve la última versión almacenada.
 */
export async function getMyNotifications() {
    const cacheKey = "faircourt_cache_notifications";

    try {
        const data = await apiRequest<Notification[]>("/notifications/me");
        saveToCache(cacheKey, data);
        return data;
    } catch (error) {
        const cached = loadFromCache<Notification[]>(cacheKey);

        if (cached) {
            return cached;
        }

        throw error;
    }
}

/**
 * Marca una notificación concreta como leída.
 *
 * @param notificationId Identificador de la notificación.
 */
export async function markNotificationAsRead(notificationId: number) {
    return apiRequest<Notification>(`/notifications/${notificationId}/read`, {
        method: "POST",
    });
}