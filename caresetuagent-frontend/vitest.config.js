import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/tests/setup.js"],
    globals: true,
    css: true,
    coverage: {
      reporter: ["text", "json", "html"],
      exclude: [
        "node_modules/",
        "src/tests/",
        "**/*.d.ts",
        "**/*.config.js",
        "dist/",
      ],
    },
    testTimeout: 10000, // 10 seconds for integration tests
    hookTimeout: 10000,
  },
  resolve: {
    alias: {
      "@": "/src",
    },
  },
});
