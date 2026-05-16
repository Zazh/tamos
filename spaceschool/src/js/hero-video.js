/* Network-aware autoplay для hero-видео на главной.
 *
 * Логика:
 * - 4g / unknown (default desktop): автоплей через 800ms после viewport intersect
 * - 3g или cellular: только click-to-play (видим большую Play-кнопку поверх poster)
 * - 2g / slow-2g / saveData: видео вообще не грузим, показываем poster + текст
 *
 * Использует navigator.connection (Network Information API). На Safari/Firefox
 * этого API нет — там по умолчанию ведём как 4g (т.к. Safari всё-таки чаще
 * desktop/wifi). Можно вручную нажать Play если автоплей не сработал.
 *
 * preload="none" на <video> — браузер не качает байты до явного .load()/.play().
 */

function detectConnection() {
  const conn = navigator.connection
    || navigator.mozConnection
    || navigator.webkitConnection;
  if (!conn) return { effective: "4g", saveData: false, supported: false };
  return {
    effective: conn.effectiveType || "4g",
    saveData: !!conn.saveData,
    supported: true,
  };
}

function heroVideo() {
  return {
    /* state переходы:
       autoplay (idle, ждём intersect)
       → playing (intersect + delay прошёл)
       → autoplay (вышел из viewport)
       click_to_play — пользователь должен нажать
       no_video — slow / saveData, видео не покажем
    */
    state: "autoplay",
    muted: true,
    delayMs: 800,
    _timer: null,

    init() {
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
        this.state = "click_to_play";
        return;
      }
      const conn = detectConnection();
      if (conn.saveData || conn.effective === "slow-2g" || conn.effective === "2g") {
        this.state = "no_video";
        return;
      }
      if (conn.effective === "3g") {
        this.state = "click_to_play";
        return;
      }
      // 4g или unsupported (Safari/Firefox) — autoplay через viewport
      this.state = "autoplay";
      this._observe();
    },

    _observe() {
      this.$nextTick(() => {
        const video = this.$refs.video;
        if (!video) return;
        new IntersectionObserver(
          ([e]) => {
            if (e.isIntersecting) {
              clearTimeout(this._timer);
              this._timer = setTimeout(() => {
                video.load();  // preload="none" — нужен явный load
                video.play().then(() => { this.state = "playing"; }).catch(() => {
                  this.state = "click_to_play";
                });
              }, this.delayMs);
            } else {
              clearTimeout(this._timer);
              if (!video.paused) video.pause();
            }
          },
          { threshold: 0 }
        ).observe(video);
      });
    },

    playManual() {
      const video = this.$refs.video;
      if (!video) return;
      video.load();
      video.play().then(() => { this.state = "playing"; }).catch(() => {});
    },

    loadAnyway() {
      this.state = "click_to_play";
    },

    toggleMute() {
      const video = this.$refs.video;
      if (!video) return;
      video.muted = !video.muted;
      this.muted = video.muted;
    },
  };
}

export function registerHeroVideo(Alpine) {
  Alpine.data("heroVideo", heroVideo);
}
