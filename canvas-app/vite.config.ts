// The frame UI → ../src/deep_reasoning/canvas_app/ui/, and vitest's configuration.
import { defineConfig } from "vitest/config";

const LIBRARY_PATHS = [
  "/health",
  "/problems",
  "/validate",
  "/profile",
  "/namespaces",
  "/effective",
  "/decompositions",
  "/tools",
];

export default defineConfig(({ command }) => ({
  base: command === "build" ? "./" : "/ui/",
  build: {
    outDir: "../src/deep_reasoning/canvas_app/ui",
    emptyOutDir: true,
    modulePreload: false,
    rollupOptions: {
      input: { app: "index.html" },
      output: {
        entryFileNames: "assets/app.js",
        assetFileNames: "assets/[name][extname]",
        inlineDynamicImports: true,
      },
    },
  },
  server: {
    proxy: Object.fromEntries(
      LIBRARY_PATHS.map((path) => [
        path,
        {
          target: process.env.DR_LIBRARY_URL ?? "http://127.0.0.1:8765",
          changeOrigin: true,
        },
      ]),
    ),
  },
  test: {
    include: ["tests/**/*.test.ts"],
    environment: "node",
  },
}));
