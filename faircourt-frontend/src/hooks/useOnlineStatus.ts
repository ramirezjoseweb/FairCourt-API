import { useEffect, useState } from "react";

/**
 * Hook encargado de detectar si el navegador tiene conexión.
 *
 * Usa:
 * - navigator.onLine para el estado inicial.
 * - eventos "online" y "offline" para actualizar el estado en tiempo real.
 *
 * @returns true si hay conexión, false si el navegador está offline.
 */
export function useOnlineStatus() {
    const [isOnline, setIsOnline] = useState(navigator.onLine);

    useEffect(() => {
        /**
         * Marca la aplicación como online cuando el navegador recupera conexión.
         */
        function handleOnline() {
            setIsOnline(true);
        }

        /**
         * Marca la aplicación como offline cuando el navegador pierde conexión.
         */
        function handleOffline() {
            setIsOnline(false);
        }

        window.addEventListener("online", handleOnline);
        window.addEventListener("offline", handleOffline);

        return () => {
            window.removeEventListener("online", handleOnline);
            window.removeEventListener("offline", handleOffline);
        };
    }, []);

    return isOnline;
}