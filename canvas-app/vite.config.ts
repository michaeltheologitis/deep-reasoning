// The frame UI → ../src/deep_reasoning/canvas_app/ui/, and vitest's configuration. The tool
// editor's CodeMirror is a chunk of its own, assets/editor.js, loaded only by the tool editor.
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
  "/mcp",
];
// Everything the "editor" chunk holds: CodeMirror, its dependencies, and our editor module.
const EDITOR_CHUNK =
  /node_modules\/(@codemirror|@lezer|style-mod|w3c-keyname|crelt)\/|src\/ui\/editor\//;

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
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name][extname]",
        inlineDynamicImports: false,
        manualChunks: (id) => (EDITOR_CHUNK.test(id) ? "editor" : undefined),
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
