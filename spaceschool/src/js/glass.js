/**
 * Glass scroll effect — updates --glass-y on .glass-secondary elements
 * based on their scroll position within the viewport.
 *
 * ──────────────────────────────────────────────────────────────────
 * USAGE (Alpine directive)
 * ──────────────────────────────────────────────────────────────────
 *
 *   <ul x-data x-glass>
 *     <li class="glass-secondary">…</li>
 *   </ul>
 *
 * The directive observes all .glass-secondary children and sets
 * --glass-y (0 → 1) as each card travels through the viewport.
 */

export function registerGlass(Alpine) {
  Alpine.directive("glass", (el, _binding, { cleanup }) => {
    const cards = el.querySelectorAll(".glass-secondary");
    if (!cards.length) return;

    function update() {
      const vh = window.innerHeight;
      for (const card of cards) {
        const rect = card.getBoundingClientRect();
        // 0 when card enters bottom, 1 when it reaches top
        const ratio = 1 - (rect.top + rect.height / 2) / vh;
        const clamped = Math.min(1, Math.max(0, ratio));
        card.style.setProperty("--glass-y", clamped.toFixed(3));
      }
    }

    let ticking = false;
    function onScroll() {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(() => {
          update();
          ticking = false;
        });
      }
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    update();

    cleanup(() => window.removeEventListener("scroll", onScroll));
  });
}
