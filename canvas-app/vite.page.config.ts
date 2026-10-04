// The page bundle → ../src/deep_reasoning/canvas_app/dist/index.js: one ES module that imports nothing.
import { defineConfig } from "vite";

export default defineConfig({
  build: {
    outDir: "../src/deep_reasoning/canvas_app/dist",
    emptyOutDir: true,
    lib: {
      entry: "src/page/index.ts",
      formats: ["es"],
      fileName: () => "index.js",
    },
  },
});
