import { apiRequest } from "./client";

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
 * El backend filtra automáticamente por household_id a partir del JWT.
 */
export async function getMyAuditLog() {
    return apiRequest<AuditLogEntry[]>("/audit/me");
}