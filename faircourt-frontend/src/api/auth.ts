import { apiRequest } from "./client";

// Tipos de datos necesarios para la API.
export type RequestOtpPayload = {
    house_code: string;
    email: string;
};

export type VerifyOtpPayload = {
    email: string;
    otp: string;
};

export type TokenResponse = {
    access_token: string;
    token_type: string;
    expires_at: string;
};

// Función para solicitar un código OTP.
export async function requestOtp(payload: RequestOtpPayload) {
    return apiRequest<{ message: string }>("/auth/request-otp", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}

// Función para verificar el código OTP y obtener el token.
export async function verifyOtp(payload: VerifyOtpPayload) {
    return apiRequest<TokenResponse>("/auth/verify-otp", {
        method: "POST",
        body: JSON.stringify(payload),
    });
}