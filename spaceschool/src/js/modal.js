const DEFAULT_TITLE = "Получить консультацию";

export function registerFeedbackModal(Alpine) {
  Alpine.store("feedback", {
    open: false,
    title: DEFAULT_TITLE,
    origin: "",
    city: false,
    show(title, origin, { city = false } = {}) {
      this.title = title && title.trim() ? title.trim() : DEFAULT_TITLE;
      this.origin = origin || (typeof window !== "undefined" ? window.location.pathname : "");
      this.city = !!city;
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
    const city = trigger.hasAttribute("data-feedback-city");
    Alpine.store("feedback").show(title, origin, { city });
  });
}
