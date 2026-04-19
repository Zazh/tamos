const DRAG_MULTIPLIER = 0.5;
const DRAG_COMMIT_RATIO = 0.12;
const FLICK_VELOCITY = 0.35;
const VELOCITY_STALE_MS = 100;

export function registerSlider(Alpine) {
  Alpine.data("teamSlider", () => ({
    canPrev: false,
    canNext: false,
    hovering: false,
    dragging: false,
    cursorX: 0,
    cursorY: 0,

    init() {
      this._startX = 0;
      this._startScroll = 0;
      this._lastX = 0;
      this._lastT = 0;
      this._velocity = 0;
      this._dragDX = 0;
      this._rafScroll = 0;
      this._pendingScroll = 0;

      this.$nextTick(() => {
        this.update();
        this.$refs.track.addEventListener("scroll", () => this.update(), { passive: true });
        new ResizeObserver(() => this.update()).observe(this.$refs.track);
      });
    },

    update() {
      const t = this.$refs.track;
      this.canPrev = t.scrollLeft > 2;
      this.canNext = t.scrollLeft + t.clientWidth < t.scrollWidth - 2;
    },

    step(dir) {
      const t = this.$refs.track;
      const size = this._cardStep();
      if (!size) return;
      t.scrollBy({ left: dir * size, behavior: "smooth" });
    },

    dragStart(e) {
      this.dragging = true;
      this._startX = e.clientX;
      this._lastX = e.clientX;
      this._lastT = performance.now();
      this._startScroll = this.$refs.track.scrollLeft;
      this._velocity = 0;
      this._dragDX = 0;
    },

    dragMove(e) {
      if (this.hovering || this.dragging) {
        this.cursorX = e.clientX;
        this.cursorY = e.clientY;
      }
      if (!this.dragging) return;

      const now = performance.now();
      const dt = now - this._lastT;
      if (dt > 0) this._velocity = (e.clientX - this._lastX) / dt;
      this._lastX = e.clientX;
      this._lastT = now;
      this._dragDX = e.clientX - this._startX;

      this._pendingScroll = this._startScroll - this._dragDX * DRAG_MULTIPLIER;
      if (this._rafScroll) return;
      this._rafScroll = requestAnimationFrame(() => {
        this.$refs.track.scrollLeft = this._pendingScroll;
        this._rafScroll = 0;
      });
    },

    dragEnd() {
      if (!this.dragging) return;
      this.dragging = false;

      const t = this.$refs.track;
      const size = this._cardStep();
      if (!size) return;

      const stale = performance.now() - this._lastT > VELOCITY_STALE_MS;
      const v = stale ? 0 : this._velocity;
      const progress = -this._dragDX / size;
      const startIndex = Math.round(this._startScroll / size);

      let delta = 0;
      if (progress > DRAG_COMMIT_RATIO || v < -FLICK_VELOCITY) delta = 1;
      else if (progress < -DRAG_COMMIT_RATIO || v > FLICK_VELOCITY) delta = -1;

      t.scrollTo({ left: (startIndex + delta) * size, behavior: "smooth" });
    },

    _cardStep() {
      const t = this.$refs.track;
      const card = t.querySelector(".team-card");
      if (!card) return 0;
      const gap = parseFloat(getComputedStyle(t).columnGap) || 0;
      return card.offsetWidth + gap;
    },
  }));
}
