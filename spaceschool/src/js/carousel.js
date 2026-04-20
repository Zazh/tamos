/**
 * Carousel scroll effect — JS-driven horizontal marquee that reacts to
 * page scroll velocity. Base auto-speed continues idle; scroll adds delta
 * with smooth decay. Overrides the CSS fallback animation when active.
 *
 * ──────────────────────────────────────────────────────────────────
 * USAGE (Alpine directive)
 * ──────────────────────────────────────────────────────────────────
 *
 *   <div class="carousel-infinity" x-data x-carousel-scroll>
 *     <ul class="carousel-track">…</ul>
 *     <ul class="carousel-track" aria-hidden="true">…</ul>
 *   </div>
 *
 * Disabled when prefers-reduced-motion is set; CSS fallback handles
 * the no-JS case.
 */

export function registerCarousel(Alpine) {
  Alpine.directive("carousel-scroll", (el, _binding, { cleanup }) => {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const tracks = el.querySelectorAll(".carousel-track");
    if (tracks.length < 2) return;

    // JS owns transforms — kill the CSS fallback animation.
    for (const t of tracks) t.style.animation = "none";

    const BASE_SPEED = 50;       // px / sec, idle drift
    const SCROLL_BOOST = 12;     // px added per 1px of page scroll delta
    const VELOCITY_DECAY = 0.92; // per frame, exponential ease-back
    const VELOCITY_MIN = 0.5;    // snap to zero below this

    let trackWidth = 0;
    let gap = 0;
    let offset = 0;
    let velocity = 0;
    let lastScrollY = window.scrollY;
    let lastFrame = performance.now();
    let visible = true;
    let rafId = 0;

    function measure() {
      trackWidth = tracks[0].offsetWidth;
      gap = parseFloat(getComputedStyle(el).gap) || 0;
    }

    function onScroll() {
      const dy = window.scrollY - lastScrollY;
      lastScrollY = window.scrollY;
      velocity += dy * SCROLL_BOOST;
    }

    function tick(now) {
      const dt = Math.min((now - lastFrame) / 1000, 0.05);
      lastFrame = now;

      const total = trackWidth + gap;
      if (total > 0 && visible) {
        offset += (BASE_SPEED + velocity) * dt;
        offset = ((offset % total) + total) % total;
        const x = (offset - total).toFixed(2);
        for (const t of tracks) {
          t.style.transform = `translate3d(${x}px, 0, 0)`;
        }
      }

      velocity = Math.abs(velocity) < VELOCITY_MIN ? 0 : velocity * VELOCITY_DECAY;

      rafId = requestAnimationFrame(tick);
    }

    measure();
    window.addEventListener("resize", measure, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });

    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; });
    io.observe(el);

    rafId = requestAnimationFrame(tick);

    cleanup(() => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", measure);
      window.removeEventListener("scroll", onScroll);
      io.disconnect();
    });
  });
}
