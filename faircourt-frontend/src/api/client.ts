const API_BASE_URL = "http://127.0.0.1:8000";

//Función auxiliar para obtener el token de localStorage.
export function getToken(): string | null {
    return localStorage.getItem("faircourt_token");
}

//Función auxiliar para hacer las peticiones a la API.
export async function apiRequest<T>(
    path: string,
    options: RequestInit = {}
): Promise<T> { // Devuelve una promesa genérica de tipo T.
    const token = getToken();

    // 1. Construye la URL completa de la petición
    const response = await fetch(`${API_BASE_URL}${path}`, {
        // 2. Propaga las opciones originales (method, body, etc.)
        ...options,
        // 3. Asegura el Content-Type
        headers: {
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {}), // Si existe token, se añade al header. (Operador ternario)
            ...(options.headers || {}), // Combina las cabeceras originales con las nuestras. (Operador ternario)
        },
    });
    // 4. Decodifica la respuesta.
    const data = await response.json().catch(() => null);
    // 5. Si la respuesta no es OK, lanza un error.
    if (!response.ok) {
        // 6. Construye el mensaje de error a partir de la respuesta o del status HTTP.
        const message =
            data?.detail || `Error HTTP ${response.status}`;
        throw new Error(message);
    }
    // 7. Devuelve los datos decodificados.
    return data as T;
}