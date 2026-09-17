import { reportReachability } from "../utils/networkStatus";

const API_BASE_URL = "http://127.0.0.1:8000";

//Función auxiliar para obtener el token de localStorage.
export function getToken(): string | null {
  return localStorage.getItem("faircourt_token");
}

export function getAdminToken(): string | null {
  return localStorage.getItem("faircourt_admin_token");
}

async function requestWithToken<T>(
  path: string,
  options: RequestInit,
  token: string | null,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {}),
      },
    });
  } catch (error) {
    reportReachability(false);
    throw error;
  }
  reportReachability(true);
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail || `Error HTTP ${response.status}`;
    throw new Error(message);
  }
  return data as T;
}

//Función auxiliar para hacer las peticiones a la API.
export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  return requestWithToken(path, options, getToken());
}

export async function adminApiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  return requestWithToken(path, options, getAdminToken());
}
