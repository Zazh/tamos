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

  build: {
    outDir: "dist",
    rollupOptions: {
      input: {
        main: resolve(__dirname, "index.html"),
        ...pages,
      },
    },
  },

  server: {
    open: true,
    port: 3000,
  },
};
