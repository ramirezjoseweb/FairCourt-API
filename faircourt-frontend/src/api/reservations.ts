import { apiRequest } from "./client";
import { loadFromCache, saveToCache } from "../utils/offlineCache";
import type { Facility } from "./facilities";

// Tipo para representar un slot.
export type Slot = {
    start_at: string;
    end_at: string;
    status: string;
    reservation_id: number | null;
    is_mine: boolean;
    can_book: boolean;
    can_join_waitlist: boolean;
    waitlist_count: number;
    in_waitlist: boolean;
    book_reason?: string | null;
    waitlist_reason?: string | null;
};

// Tipo para representar una reserva.
export type Reservation = {
    id: number;
    household_id: number;
    facility_id: number;
    facility: Facility;
    start_at: string;
    end_at: string;
    status: string;
    created_at: string;
    real_status?: string;
};

/**
 * Respuesta generada por el backend para realizar check-in.
 *
 * Contiene la URL firmada que permite validar la asistencia
 * dentro de la ventana temporal permitida.
 */
export type CheckinQrResponse = {
    reservation_id: number;
    checkin_url: string;
    expires_at: string;
};

/**
 * Solicita al backend la URL de check-in de una reserva.
 *
 * @param reservationId Identificador de la reserva.
 */
export async function getCheckinQr(reservationId: number) {
    return apiRequest<CheckinQrResponse>(
        `/reservations/${reservationId}/checkin-qr`
    );
}

/**
 * Consulta las franjas disponibles para un día concreto.
 *
 * Si hay conexión, guarda la respuesta en caché.
 * Si la petición falla, intenta devolver los últimos slots guardados para ese día.
 *
 * @param day Fecha en formato YYYY-MM-DD.
 */
export async function getSlots(day: string, facilityId: number) {
    const cacheKey = `faircourt_cache_slots_${facilityId}_${day}`;

    try {
        const data = await apiRequest<Slot[]>(
            `/reservations/slots?day=${day}&facility_id=${facilityId}`
        );
        saveToCache(cacheKey, data);
        return data;
    } catch (error) {
        const cached = loadFromCache<Slot[]>(cacheKey);

        if (cached) {
            return cached;
        }

        throw error;
    }
}

// Función para crear una reserva.
export async function createReservation(facilityId: number, startAt: string) {
    return apiRequest<Reservation>("/reservations", {
        method: "POST",
        body: JSON.stringify({
            facility_id: facilityId,
            start_at: startAt,
        }),
    });
}

// Función para unirse a la lista de espera.
export async function joinWaitlist(facilityId: number, startAt: string) {
    return apiRequest<{
        id: number;
        facility_id: number;
        facility: Facility;
        start_at: string;
        household_id: number;
        created_at: string;
        status: string;
    }>("/reservations/waitlist", {
        method: "POST",
        body: JSON.stringify({
            facility_id: facilityId,
            start_at: startAt,
        }),
    });
}

/**
 * Obtiene todas las reservas asociadas a la vivienda autenticada.
 *
 * Si el backend responde correctamente, guarda la respuesta en caché.
 * Si no hay conexión, devuelve las últimas reservas guardadas.
 */
export async function getMyReservations() {
    const cacheKey = "faircourt_cache_reservations";

    try {
        const data = await apiRequest<Reservation[]>("/reservations/me");
        saveToCache(cacheKey, data);
        return data;
    } catch (error) {
        const cached = loadFromCache<Reservation[]>(cacheKey);

        if (cached) {
            return cached;
        }

        throw error;
    }
}

/**
 * Cancela una reserva existente.
 *
 * @param reservationId Identificador de la reserva a cancelar.
 */
export async function cancelReservation(reservationId: number) {
    return apiRequest<Reservation>(`/reservations/${reservationId}/cancel`, {
        method: "POST",
    });
}
