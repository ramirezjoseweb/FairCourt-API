import { apiRequest } from "./client";

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
 * El backend filtra por household_id usando el JWT del usuario actual.
 */
export async function getMyNotifications() {
    return apiRequest<Notification[]>("/notifications/me");
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