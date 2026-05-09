import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { registerSW } from "virtual:pwa-register";
import "./index.css";
import App from "./App.tsx";

/**
 * Registro del Service Worker generado por vite-plugin-pwa.
 *
 * registerType: "autoUpdate" en vite.config.ts permite que el service worker
 * busque nuevas versiones de la aplicación y las actualice automáticamente.
 */
registerSW({
  immediate: true,
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);