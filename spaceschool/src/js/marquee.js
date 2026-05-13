/**
 * Marquee: «бегущая строка», если контент шире контейнера.
 *
 * Использование в шаблоне:
 *   <span class="marquee"><span class="marquee-inner">long text…</span></span>
 *
 * Скрипт измеряет overflow, выставляет CSS-переменную --marquee-shift и
 * включает класс `is-overflowing`. CSS уже содержит keyframes на этот класс
 * (см. accordion.css). Если контент влезает — анимации нет.
 *
 * Важно мерить после `document.fonts.ready` — иначе DOMContentLoaded
 * сработает на системном fallback-шрифте, scrollWidth будет занижен,
 * и в крайнем положении правый край текста не успеет вылезти из-под
 * правого многоточия (классическая жалоба «текст обрезается в конце»).
 */

// Запас на subpixel-rounding и ширину pseudo-элемента «…» (если он рендерится
// плотно к правому краю при остановке). Текст уезжает на эти пиксели дальше,
// чем расчётный overflow → правый край гарантированно виден в крайней позиции.
const OVERSHOOT_PX = 4;

function measureOne(el) {
  const inner = el.querySelector(".marquee-inner");
  if (!inner) return;
  // Display:none / hidden parents → 0. В этом случае не пытаемся анимировать —
  // обновим, когда контейнер станет видимым (через ResizeObserver).
  const containerW = el.clientWidth;
  const innerW = inner.scrollWidth;
  if (containerW === 0) return;
  if (innerW > containerW + 1) {
    const shift = containerW - innerW - OVERSHOOT_PX;
    inner.style.setProperty("--marquee-shift", `${shift}px`);
    el.classList.add("is-overflowing");
  } else {
    inner.style.removeProperty("--marquee-shift");
    el.classList.remove("is-overflowing");
  }
}

function measureAll() {
  document.querySelectorAll(".marquee").forEach(measureOne);
}

let raf = 0;
function scheduleMeasure() {
  cancelAnimationFrame(raf);
  raf = requestAnimationFrame(measureAll);
}

export function initMarquee() {
  const setup = () => {
    measureAll();
    if (typeof ResizeObserver !== "undefined") {
      // Пересчёт когда контейнер ресайзится (фильтр, открытие аккордеона,
      // адаптив).
      const ro = new ResizeObserver(scheduleMeasure);
      document.querySelectorAll(".marquee").forEach((el) => ro.observe(el));
    }
  };

  // Шрифты могут грузиться дольше HTML/CSS. Мерим только после их готовности.
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(setup);
  } else {
    // Fallback для старых браузеров без CSS Font Loading API.
    if (document.readyState === "complete") {
      setup();
    } else {
      window.addEventListener("load", setup, { once: true });
    }
  }

  window.addEventListener("resize", scheduleMeasure, { passive: true });
}
