import "../css/main.css";
import Alpine from "alpinejs";
import collapse from "@alpinejs/collapse";
import fitty from "fitty";
import { registerStarfield } from "./starfield.js";
import { registerGlass } from "./glass.js";
import { registerSlider } from "./slider.js";

Alpine.plugin(collapse);
registerStarfield(Alpine);
registerGlass(Alpine);
registerSlider(Alpine);


window.Alpine = Alpine;
Alpine.start();

/* Meteor parallax */
document.addEventListener("DOMContentLoaded", () => {
  const meteors = document.querySelectorAll(".hero-meteor");
  if (!meteors.length) return;

  let scrollY = 0;
  let mouseX = 0;
  let mouseY = 0;
  let ticking = false;

  function update() {
    meteors.forEach((el) => {
      const speed = parseFloat(el.dataset.speed) || 0;
      const sy = scrollY * speed;
      const mx = mouseX * speed * 30;
      const my = mouseY * speed * 30;
      const rotSpeed = parseFloat(el.dataset.rotate) || 40;
      const rot = (mouseX + mouseY) * rotSpeed;
      el.style.transform = `translate(${mx}px, ${sy + my}px) rotate(${rot}deg)`;
    });
    ticking = false;
  }

  function requestUpdate() {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(update);
    }
  }

  window.addEventListener("scroll", () => {
    scrollY = window.scrollY;
    requestUpdate();
  }, { passive: true });

  window.addEventListener("mousemove", (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    requestUpdate();
  }, { passive: true });
});

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
