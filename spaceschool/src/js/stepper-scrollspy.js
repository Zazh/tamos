/**
 * Stepper scrollspy: переключает .active у `.stepper-step` по тому,
 * какой `.stage-header[data-stage]` сейчас в верхней зоне вьюпорта.
 *
 * Десктоп (lg+): триггер — верхняя треть вьюпорта, sticky aside в колонке.
 * Мобиле: триггер — нижний край sticky-бара stepper'а; активный шаг
 *   меняет gold-fill маркера и подпись в .stepper-current под трекером.
 *
 * Клик по шагу скроллит к стадии (с offset под sticky на мобиле).
 *
 * Используется на admission.html. Активируется по `<aside data-stepper-spy>`.
 */

const LG_BREAKPOINT = "(min-width: 1024px)";
const TRIGGER_RATIO_LG = 0.3;
const STICKY_TOP_LG = 32; // соответствует `lg:top-8` (2rem) у aside в admission.html

export function initStepperScrollspy() {
  document.querySelectorAll("[data-stepper-spy]").forEach(initOne);
}

function initOne(spy) {
  const steps = Array.from(spy.querySelectorAll(".stepper-step[data-stage]"));
  const stages = Array.from(document.querySelectorAll(".stage-header[data-stage]"));
  if (!steps.length || !stages.length) return;

  stages.sort((a, b) =>
    a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1
  );

  const currentNumEl = spy.querySelector("[data-stepper-current] .stepper-current__num");
  const currentTitleEl = spy.querySelector("[data-stepper-current] .stepper-current__title");

  const mq = window.matchMedia(LG_BREAKPOINT);
  let currentStage = null;
  let ticking = false;

  function setActive(stage) {
    if (stage === currentStage) return;
    currentStage = stage;
    steps.forEach((step) => {
      step.classList.toggle("active", step.dataset.stage === stage);
    });
    updateCurrentText(stage);
  }

  function updateCurrentText(stage) {
    if (!currentNumEl && !currentTitleEl) return;
    const stageEl = stages.find((s) => s.dataset.stage === stage);
    const titleEl = stageEl && stageEl.querySelector(".stage-header__title");
    if (!titleEl) return;

    const fullText = titleEl.textContent.trim().replace(/\s+/g, " ");
    const match = fullText.match(/^(\d+)\s*[—-]\s*(.+)$/);
    if (match) {
      if (currentNumEl) currentNumEl.textContent = match[1];
      if (currentTitleEl) currentTitleEl.textContent = match[2];
    } else {
      if (currentNumEl) currentNumEl.textContent = String(stage).padStart(2, "0");
      if (currentTitleEl) currentTitleEl.textContent = fullText;
    }
  }

  function update() {
    ticking = false;
    const isDesktop = mq.matches;
    const stickyTop = isDesktop ? STICKY_TOP_LG : 0;
    const triggerY = isDesktop
      ? window.innerHeight * TRIGGER_RATIO_LG
      : spy.getBoundingClientRect().bottom + 16;

    let active = stages[0].dataset.stage;
    for (const el of stages) {
      if (el.getBoundingClientRect().top <= triggerY) {
        active = el.dataset.stage;
      } else {
        break;
      }
    }

    // Финальная стадия может быть слишком короткой — её заголовок не доходит
    // до триггерной линии. Sticky-aside «отлипает» от верха, когда контейнер
    // исчерпан → это и есть «пользователь дошёл до конца», форсим последний шаг.
    if (spy.getBoundingClientRect().top < stickyTop - 1) {
      active = stages[stages.length - 1].dataset.stage;
    }

    setActive(active);
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(update);
  }

  function scrollToStage(stage) {
    if (mq.matches) {
      stage.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    const stickyHeight = spy.offsetHeight;
    const top =
      window.scrollY + stage.getBoundingClientRect().top - stickyHeight - 8;
    window.scrollTo({ top, behavior: "smooth" });
  }

  steps.forEach((step) => {
    step.style.cursor = "pointer";
    step.addEventListener("click", () => {
      const target = stages.find((s) => s.dataset.stage === step.dataset.stage);
      if (target) scrollToStage(target);
    });
  });

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });
  mq.addEventListener("change", () => {
    currentStage = null;
    onScroll();
  });

  update();
}
