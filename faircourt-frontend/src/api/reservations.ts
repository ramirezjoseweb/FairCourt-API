import { apiRequest } from "./client";

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

// Función para obtener los slots de un día.
export async function getSlots(day: string) {
    return apiRequest<Slot[]>(`/reservations/slots?day=${day}`);
}

// Función para crear una reserva.
export async function createReservation(startAt: string) {
    return apiRequest<Reservation>("/reservations", {
        method: "POST",
        body: JSON.stringify({
            start_at: startAt,
        }),
    });
}

// Función para unirse a la lista de espera.
export async function joinWaitlist(startAt: string) {
    return apiRequest<{
        id: number;
        start_at: string;
        household_id: number;
        created_at: string;
        status: string;
    }>("/reservations/waitlist", {
        method: "POST",
        body: JSON.stringify({
            start_at: startAt,
        }),
    });
}

// Función para obtener las reservas del usuario actual.
export async function getMyReservations() {
    return apiRequest<Reservation[]>("/reservations/me");
}

// Función para cancelar una reserva.
export async function cancelReservation(reservationId: number) {
    return apiRequest<Reservation>(`/reservations/${reservationId}/cancel`, {
        method: "POST",
    });
}