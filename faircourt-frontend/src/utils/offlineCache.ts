import { getCommunitySlug } from "./community";

function storageKey(key: string): string {
    return `${key}__${getCommunityCacheScope()}`;
}

function getCommunityCacheScope(): string {
    const token = localStorage.getItem("faircourt_token");
    if (token) {
        try {
            const encodedPayload = token.split(".")[1];
            const base64 = encodedPayload
                .replace(/-/g, "+")
                .replace(/_/g, "/")
                .padEnd(Math.ceil(encodedPayload.length / 4) * 4, "=");
            const payload = JSON.parse(atob(base64)) as {
                community_id?: number;
            };
            if (payload.community_id) {
                return `community-${payload.community_id}`;
            }
        } catch {
            // Los fixtures y tokens antiguos pueden no contener claims legibles.
        }
    }
    return getCommunitySlug();
}

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
            storageKey(key),
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
        const rawValue = localStorage.getItem(storageKey(key));

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
        const rawValue = localStorage.getItem(storageKey(key));

        if (!rawValue) {
            return null;
        }

        const parsed = JSON.parse(rawValue);

        return parsed.saved_at ?? null;
    } catch {
        return null;
    }
}

export function clearCommunityCache(): void {
    const suffix = `__${getCommunityCacheScope()}`;
    for (let index = localStorage.length - 1; index >= 0; index -= 1) {
        const key = localStorage.key(index);
        if (key?.startsWith("faircourt_cache_") && key.endsWith(suffix)) {
            localStorage.removeItem(key);
        }
    }
}
