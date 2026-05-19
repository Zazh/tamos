/* Decorative looping video (без UI, без звука).
 *
 * Использование:
 *   <div x-data="ambientVideo">
 *     <video x-ref="video" preload="none" muted loop playsinline
 *            poster="..."><source src="..." type="video/mp4"></video>
 *   </div>
 *
 * Что делает:
 * - preload="none" → байты не качаются, пока ролик не попал во вьюпорт
 * - на intersect: video.load() + video.play()
 * - вышел из вьюпорта → video.pause() (CPU/декодер)
 * - вернулся → play() (loop продолжается с того же кадра)
 *
 * UI/тосты/click-to-play намеренно отсутствуют: это декорация.
 * Для контентного видео со звуком и кнопками — heroVideo.
 */

export function registerAmbientVideo(Alpine) {
  Alpine.data("ambientVideo", () => ({
    _loaded: false,

    init() {
      this.$nextTick(() => {
        const video = this.$refs.video;
        if (!video) return;
        new IntersectionObserver(
          ([e]) => {
            if (e.isIntersecting) {
              if (!this._loaded) {
                video.load();
                this._loaded = true;
              }
              const p = video.play();
              if (p && p.catch) p.catch(() => {});
            } else if (!video.paused) {
              video.pause();
            }
          },
          { threshold: 0 }
        ).observe(video);
      });
    },
  }));
}
