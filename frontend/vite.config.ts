import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "^/(config_schema|input_schema|stream|assistants|threads|ingest|feedback)":
        {
          target: "http://127.0.0.1:8100",
          changeOrigin: true,
          rewrite: (path) => path.replace("/____LANGSERVE_BASE_URL", ""),
        },
    },
  },
});
