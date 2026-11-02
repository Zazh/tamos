/* Заголовок по умолчанию НЕ хардкодим здесь: JS не знает активный язык.
 * Пустой title → шаблон `partials/modals/feedback.html` подставляет
 * `defaultTitle` из x-data, который отрендерен через {% trans %}.
 * То же для lead: пусто → defaultLead шаблона.
 *
 * Атрибуты триггера [data-feedback-trigger]:
 *   data-feedback-title / -origin — заголовок и источник заявки (Lead.title / origin);
 *   data-feedback-lead            — подзаголовок формы;
 *   data-feedback-price           — строка цены над кнопкой «Отправить»;
 *   data-feedback-parent-checkbox="1" — чекбокс «Я родитель ученика Space School» (→ Lead.extra);
 *   data-feedback-success         — доп. строка успеха под «Перезвоним вам в течение 2 часов». */

const EMPTY = { title: "", origin: "", lead: "", price: "", parentCheckbox: false, success: "" };

export function registerFeedbackModal(Alpine) {
  Alpine.store("feedback", {
    open: false,
    ...EMPTY,
    show(trigger) {
      const d = (trigger && trigger.dataset) || {};
      const clean = (v) => (v && v.trim() ? v.trim() : "");
      this.title = clean(d.feedbackTitle);
      this.origin = d.feedbackOrigin || (typeof window !== "undefined" ? window.location.pathname : "");
      this.lead = clean(d.feedbackLead);
      this.price = clean(d.feedbackPrice);
      this.parentCheckbox = d.feedbackParentCheckbox === "1";
      this.success = clean(d.feedbackSuccess);
      this.open = true;
    },
    hide() {
      this.open = false;
      Object.assign(this, EMPTY);
    },
  });

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-feedback-trigger]");
    if (!trigger) return;
    event.preventDefault();
    Alpine.store("feedback").show(trigger);
  });
}
