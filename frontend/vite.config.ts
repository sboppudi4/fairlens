import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
  },
  build: {
    // Split rarely-changing vendor code into its own long-lived cache entries so
    // an app-code change doesn't invalidate the (large) third-party bundles, and
    // so the heavy charting/animation libs are isolated to the routes that use them.
    rollupOptions: {
      output: {
        manualChunks: {
          "react-vendor": ["react", "react-dom", "react-router-dom"],
          query: ["@tanstack/react-query"],
          charts: ["recharts"],
          motion: ["framer-motion"],
          three: ["three", "@react-three/fiber"],
        },
      },
    },
  },
});
