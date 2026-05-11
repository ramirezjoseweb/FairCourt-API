/**
 * Guarda un valor JSON en localStorage.
 *
 * Se usa para conservar la última respuesta válida del backend y poder
 * mostrarla cuando la aplicación esté sin conexión.
 *
 * @param key Clave de almacenamiento.
 * @param value Valor que se quiere guardar.
 */
export function saveToCache<T>(key: string, value: T): void {
    try {
        localStorage.setItem(
            key,
            JSON.stringify({
                saved_at: new Date().toISOString(),
                data: value,
            })
        );
    } catch {
        // Si localStorage falla, no rompemos la aplicación.
    }
}

/**
 * Recupera un valor JSON previamente guardado en localStorage.
 *
 * @param key Clave de almacenamiento.
 * @returns El valor cacheado o null si no existe.
 */
export function loadFromCache<T>(key: string): T | null {
    try {
        const rawValue = localStorage.getItem(key);

        if (!rawValue) {
            return null;
        }

        const parsed = JSON.parse(rawValue);

        return parsed.data as T;
    } catch {
        return null;
    }
}

/**
 * Recupera la fecha en la que se guardó un valor cacheado.
 *
 * @param key Clave de almacenamiento.
 * @returns Fecha ISO de guardado o null si no existe.
 */
export function getCacheSavedAt(key: string): string | null {
    try {
        const rawValue = localStorage.getItem(key);

        if (!rawValue) {
            return null;
        }

        const parsed = JSON.parse(rawValue);

        return parsed.saved_at ?? null;
    } catch {
        return null;
    }
}