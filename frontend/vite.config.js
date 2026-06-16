import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://localhost:8000",
      "/notebooks": "http://localhost:8000",
      "/chat": "http://localhost:8000",
      "/notes": "http://localhost:8000",
      "/memory": "http://localhost:8000"
    }
  }
});
