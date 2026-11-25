import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // The app calls the API at /api on its own origin; in development that is
    // forwarded to the Django server.
    proxy: {
      "/api": process.env.VITE_PROXY_TARGET ?? "http://127.0.0.1:8000",
    },
  },
});
