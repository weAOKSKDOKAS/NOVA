import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Vite dev server on :5173; the API base is configurable via VITE_API_BASE.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173, host: true },
});
