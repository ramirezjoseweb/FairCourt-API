import { apiRequest } from "./client";
//Tipos de datos necesarios para la API.
export type MeResponse = {
    id: number;
    email: string;
    household_id: number;
    household_code?: string | null;
    strikes?: number;
    suspended_until?: string | null;
    active_waitlists_count?: number;
};

// Función para obtener la información del usuario.
export async function getMe() {
    return apiRequest<MeResponse>("/me");
}