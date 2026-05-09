import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";

/**
 * Configuración principal de Vite.
 *
 * Además de React y Tailwind, se añade el plugin PWA para:
 * - generar manifest,
 * - registrar service worker,
 * - permitir instalación de la app,
 * - cachear recursos estáticos del frontend.
 */
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "autoUpdate",

      includeAssets: ["favicon.svg"],

      manifest: {
        name: "FairCourt",
        short_name: "FairCourt",
        description: "Sistema justo de reservas comunitarias",
        theme_color: "#0f172a",
        background_color: "#f1f5f9",
        display: "standalone",
        start_url: "/",
        scope: "/",

        icons: [
          {
            src: "/pwa-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "/pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
        ],
      },

      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg}"],
      },

      devOptions: {
        enabled: true,
      },
    }),
  ],
});