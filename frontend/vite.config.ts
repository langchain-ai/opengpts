import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "^/(config_schema|input_schema|stream)": {
        target: "http://opengpts-backend:8100",
        changeOrigin: true,
        rewrite: (path) => path.replace("/____LANGSERVE_BASE_URL", ""),
      },
    },
  },
});
