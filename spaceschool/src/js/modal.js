/* Заголовок по умолчанию НЕ хардкодим здесь: JS не знает активный язык.
 * Пустой title → шаблон `partials/modals/feedback.html` подставляет
 * `defaultTitle` из x-data, который отрендерен через {% trans %}. */

export function registerFeedbackModal(Alpine) {
  Alpine.store("feedback", {
    open: false,
    title: "",
    origin: "",
    show(title, origin) {
      this.title = title && title.trim() ? title.trim() : "";
      this.origin = origin || (typeof window !== "undefined" ? window.location.pathname : "");
      this.open = true;
    },
    hide() {
      this.open = false;
    },
  });

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-feedback-trigger]");
    if (!trigger) return;
    event.preventDefault();
    const title = trigger.getAttribute("data-feedback-title");
    const origin = trigger.getAttribute("data-feedback-origin");
    Alpine.store("feedback").show(title, origin);
  });
}
