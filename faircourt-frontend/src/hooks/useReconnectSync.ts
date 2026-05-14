import { useEffect, useRef } from "react";

/**
 * Hook que ejecuta una función cuando la aplicación recupera conexión.
 *
 * Evita ejecutarse en el primer render y solo dispara la sincronización
 * cuando el estado cambia de offline a online.
 *
 * @param isOnline Estado actual de conexión.
 * @param onReconnect Función que se ejecuta al recuperar conexión.
 */
export function useReconnectSync(
    isOnline: boolean,
    onReconnect: () => void | Promise<void>
) {
    const wasOnlineRef = useRef(isOnline);

    useEffect(() => {
        const wasOnline = wasOnlineRef.current;

        if (!wasOnline && isOnline) {
            onReconnect();
        }

        wasOnlineRef.current = isOnline;
    }, [isOnline, onReconnect]);
}