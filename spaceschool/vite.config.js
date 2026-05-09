import { resolve } from "path";
import { readdirSync } from "fs";
import tailwindcss from "@tailwindcss/vite";

// Автоматически собираем все HTML-файлы из pages/
const pages = readdirSync(resolve(__dirname, "pages"))
  .filter((f) => f.endsWith(".html"))
  .reduce((entries, file) => {
    const name = file.replace(".html", "");
    entries[name] = resolve(__dirname, "pages", file);
    return entries;
  }, {});

export default {
  plugins: [tailwindcss()],

  root: ".",
  base: "/static/",

  build: {
    outDir: "../static",
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, "src/js/main.js"),
        index: resolve(__dirname, "index.html"),
        ...pages,
      },
      output: {
        entryFileNames: "assets/js/[name]-[hash].js",
        chunkFileNames: "assets/js/[name]-[hash].js",
        assetFileNames: (assetInfo) => {
          const name = assetInfo.name ?? "";
          const ext = name.split(".").pop()?.toLowerCase() ?? "";
          if (ext === "css") return "assets/css/[name]-[hash][extname]";
          if (["png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "avif"].includes(ext))
            return "assets/images/[name]-[hash][extname]";
          if (["woff", "woff2", "ttf", "otf", "eot"].includes(ext))
            return "assets/fonts/[name]-[hash][extname]";
          return "assets/[name]-[hash][extname]";
        },
      },
    },
  },

  server: {
    open: true,
    port: 3000,
    origin: "http://localhost:3000",
    cors: true,
  },
};
