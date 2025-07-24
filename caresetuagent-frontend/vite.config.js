import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  // Build configuration for production
  build: {
    // Output directory for production build
    outDir: "dist",

    // Generate source maps for debugging in production
    sourcemap: true,

    // Optimize bundle size
    minify: "terser",

    // Configure chunk splitting for better caching
    rollupOptions: {
      output: {
        manualChunks: {
          // Separate vendor chunks for better caching
          vendor: ["react", "react-dom"],
          livekit: ["livekit-client", "@livekit/components-react"],
        },
      },
    },

    // Asset optimization
    assetsDir: "assets",

    // Increase chunk size warning limit for LiveKit dependencies
    chunkSizeWarningLimit: 1000,
  },

  // Development server configuration
  server: {
    port: 3000,
    host: true, // Allow external connections
    open: true, // Auto-open browser
  },

  // Preview server configuration (for testing production build)
  preview: {
    port: 4173,
    host: true,
  },

  // Base path configuration for different deployment environments
  base: process.env.NODE_ENV === "production" ? "/" : "/",

  // Define global constants
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version || "1.0.0"),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },
});
