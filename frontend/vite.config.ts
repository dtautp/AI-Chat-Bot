import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    build: {
        //outDir: "../backend/static",
        emptyOutDir: true,
        sourcemap: true
    },
    server: {
        proxy: {
            // "/chat": "https://saltoeusutpback01dev.azurewebsites.net"
            "/chat": "http://0.0.0.0:5000"
        }
    }
});
