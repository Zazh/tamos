/**
 * Starfield — canvas-based animated star background.
 *
 * Renders a randomized starfield behind the content of any element.
 * Stars are generated based on the element's area, so density adapts
 * automatically to different screen sizes (fewer stars on mobile).
 *
 * ──────────────────────────────────────────────────────────────────
 * USAGE (Alpine directive)
 * ──────────────────────────────────────────────────────────────────
 *
 *   <!-- All defaults -->
 *   <section x-data x-starfield>
 *
 *   <!-- With presets -->
 *   <section x-data x-starfield="{ density: 'high', twinkle: 'low', shooting: 'medium' }">
 *
 *   <!-- Mix presets and exact values -->
 *   <section x-data x-starfield="{ density: 45, twinkle: 'high', shooting: 0 }">
 *
 * ──────────────────────────────────────────────────────────────────
 * OPTIONS
 * ──────────────────────────────────────────────────────────────────
 *
 *   density   "low" | "medium" | "high" | number     default: "medium"
 *             Stars per 100 000 px² of container area.
 *             Presets: low = 30, medium = 60, high = 100.
 *             Accepts any positive number for fine-tuning.
 *
 *   twinkle   "low" | "medium" | "high" | number     default: "medium"
 *             Fraction of stars that pulsate (0–1).
 *             Presets: low = 0.1 (10%), medium = 0.2 (20%), high = 0.4 (40%).
 *             Each twinkling star gets a random speed and phase offset.
 *
 *   shooting  "low" | "medium" | "high" | number     default: "medium"
 *             Interval in ms between shooting stars. 0 = disabled.
 *             Presets: low = 8 000 ms, medium = 5 000 ms, high = 2 500 ms.
 *
 *   color     any CSS color string                    default: "white"
 *             Applied to all stars and shooting-star tails.
 *
 *   opacity   number 0–1                              default: 0.7
 *             Base brightness multiplier for every star.
 *             Individual stars vary randomly within this range;
 *             twinkling stars modulate on top of it.
 *
 * ──────────────────────────────────────────────────────────────────
 * NOTE: The host element must have `position: relative` (or absolute/fixed)
 * so the canvas is positioned correctly behind its content.
 */

// ---------------------------------------------------------------------------
// Presets & resolution
// ---------------------------------------------------------------------------

const PRESETS = {
  density:  { low: 30, medium: 60, high: 100 },
  twinkle:  { low: 0.1, medium: 0.2, high: 0.4 },
  shooting: { low: 8000, medium: 5000, high: 2500 },
};

function resolve(key, value) {
  if (value == null) return PRESETS[key].medium;
  if (typeof value === "string") return PRESETS[key][value] ?? PRESETS[key].medium;
  return value;
}

function resolveOptions(raw) {
  return {
    density: resolve("density", raw.density),
    twinkleRatio: resolve("twinkle", raw.twinkle),
    shootingInterval: resolve("shooting", raw.shooting),
    color: raw.color ?? "white",
    opacity: raw.opacity ?? 0.7,
  };
}

// ---------------------------------------------------------------------------
// Star generation
// ---------------------------------------------------------------------------

function generateStars(w, h, opts) {
  const count = Math.round((w * h / 100_000) * opts.density);
  const stars = new Array(count);

  for (let i = 0; i < count; i++) {
    stars[i] = {
      x: Math.random() * w,
      y: Math.random() * h,
      r: Math.random() < 0.3 ? 1.2 : 0.6,
      baseAlpha: 0.4 + Math.random() * 0.6,
      twinkle: Math.random() < opts.twinkleRatio,
      twinkleSpeed: 0.5 + Math.random() * 2,
      twinkleOffset: Math.random() * Math.PI * 2,
    };
  }

  return stars;
}

// ---------------------------------------------------------------------------
// Shooting star
// ---------------------------------------------------------------------------

function createShootingStar(w, h) {
  return {
    x: Math.random() * w * 0.8,
    y: Math.random() * h * 0.4,
    angle: Math.PI / 6 + Math.random() * (Math.PI / 6),
    speed: 3 + Math.random() * 4,
    length: 40 + Math.random() * 60,
    life: 1,
    decay: 0.012 + Math.random() * 0.008,
  };
}

function updateShootingStar(ss) {
  ss.x += Math.cos(ss.angle) * ss.speed;
  ss.y += Math.sin(ss.angle) * ss.speed;
  ss.life -= ss.decay;
  return ss.life > 0;
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

function drawStars(ctx, stars, time, opts) {
  const t = time / 1000;

  for (const s of stars) {
    let alpha = s.baseAlpha * opts.opacity;
    if (s.twinkle) {
      const wave = (Math.sin(t * s.twinkleSpeed + s.twinkleOffset) + 1) / 2;
      alpha *= 0.4 + 0.6 * wave;
    }
    ctx.globalAlpha = alpha;
    ctx.fillStyle = opts.color;
    ctx.beginPath();
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawShootingStar(ctx, ss, opts) {
  const tailX = ss.x - Math.cos(ss.angle) * ss.length;
  const tailY = ss.y - Math.sin(ss.angle) * ss.length;
  const grad = ctx.createLinearGradient(tailX, tailY, ss.x, ss.y);

  grad.addColorStop(0, "transparent");
  grad.addColorStop(1, opts.color);

  ctx.globalAlpha = ss.life * 0.8;
  ctx.strokeStyle = grad;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(tailX, tailY);
  ctx.lineTo(ss.x, ss.y);
  ctx.stroke();
}

// ---------------------------------------------------------------------------
// Main loop
// ---------------------------------------------------------------------------

function createStarfield(canvas, userOpts = {}) {
  const opts = resolveOptions(userOpts);
  const ctx = canvas.getContext("2d");

  let stars = [];
  let shootingStar = null;
  let w = 0;
  let h = 0;
  let animId;

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    w = canvas.width = rect.width;
    h = canvas.height = rect.height;
    stars = generateStars(w, h, opts);
  }

  function frame(time) {
    ctx.clearRect(0, 0, w, h);

    drawStars(ctx, stars, time, opts);

    if (shootingStar) {
      const alive = updateShootingStar(shootingStar);
      if (alive) {
        drawShootingStar(ctx, shootingStar, opts);
      } else {
        shootingStar = null;
      }
    }

    ctx.globalAlpha = 1;
    animId = requestAnimationFrame(frame);
  }

  // Init
  resize();
  animId = requestAnimationFrame(frame);

  const ro = new ResizeObserver(resize);
  ro.observe(canvas.parentElement);

  // Shooting stars scheduler
  let shootingTimer = null;
  if (opts.shootingInterval) {
    shootingTimer = setInterval(() => { shootingStar = createShootingStar(w, h); }, opts.shootingInterval);
    setTimeout(() => { shootingStar = createShootingStar(w, h); }, 1000 + Math.random() * 2000);
  }

  // Cleanup
  return () => {
    cancelAnimationFrame(animId);
    ro.disconnect();
    if (shootingTimer) clearInterval(shootingTimer);
  };
}

// ---------------------------------------------------------------------------
// Alpine directive
// ---------------------------------------------------------------------------

export function registerStarfield(Alpine) {
  Alpine.directive("starfield", (el, { expression }, { evaluate, cleanup }) => {
    const opts = expression ? evaluate(expression) : {};

    const canvas = document.createElement("canvas");
    canvas.style.cssText = "position:absolute;inset:0;pointer-events:none;width:100%;height:100%;";
    el.insertBefore(canvas, el.firstChild);

    const destroy = createStarfield(canvas, opts);

    cleanup(() => {
      destroy();
      canvas.remove();
    });
  });
}
