import "../css/main.css";
import Alpine from "alpinejs";
import collapse from "@alpinejs/collapse";
import fitty from "fitty";
import { registerStarfield } from "./starfield.js";
import { registerGlass } from "./glass.js";

Alpine.plugin(collapse);
registerStarfield(Alpine);
registerGlass(Alpine);


window.Alpine = Alpine;
Alpine.start();

document.fonts.ready.then(() => {
  const md = window.matchMedia("(min-width: 768px)");

  function applyFitty() {
    if (md.matches) return;

    const fits = fitty(".hero-fit", { maxSize: 40 });

    Promise.all(fits.map(f => new Promise(r => f.element.addEventListener("fit", r, { once: true }))))
      .then(() => {
        const minSize = Math.min(...fits.map(f => parseFloat(f.element.style.fontSize)));
        fits.forEach(f => {
          f.unsubscribe();
          f.element.style.fontSize = minSize + "px";
        });
      });
  }

  function clearFitty() {
    document.querySelectorAll(".hero-fit").forEach(el => el.style.fontSize = "");
  }

  md.addEventListener("change", () => md.matches ? clearFitty() : applyFitty());
  applyFitty();
});
