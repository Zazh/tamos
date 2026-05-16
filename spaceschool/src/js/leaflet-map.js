import L from "leaflet";
import "leaflet/dist/leaflet.css";

// CartoDB Positron Light (no labels) — нейтральная подложка под наш дизайн.
// https://github.com/CartoDB/basemap-styles
const TILE_URL = "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png";

// Файл лежит в `spaceschool/public/images/icons/` → Vite кладёт его в
// `static/images/icons/` (см. memory/directory-layout.md). Стабильный URL.
// SVG-viewBox 512×512, золотой треугольный кончик в точке (256, 456) ≈ (50%, 89%).
const MARKER_ICON = L.icon({
  iconUrl: "/static/images/icons/pointer-map.svg",
  iconSize: [40, 40],
  iconAnchor: [20, 36], // кончик указателя в этой пиксель-координате
});

function parseCoordinates(value) {
  if (!value) return null;
  const [latStr, lngStr] = value.split(",");
  const lat = parseFloat(latStr);
  const lng = parseFloat(lngStr);
  if (Number.isNaN(lat) || Number.isNaN(lng)) return null;
  return [lat, lng];
}

function initMap(el) {
  const center = parseCoordinates(el.dataset.coordinates);
  if (!center) return;

  const zoom = parseInt(el.dataset.zoom, 10) || 16;

  const map = L.map(el, {
    center,
    zoom,
    scrollWheelZoom: false,
    zoomControl: true,
    attributionControl: false,
  });

  L.tileLayer(TILE_URL, {
    maxZoom: 19,
  }).addTo(map);

  L.marker(center, { icon: MARKER_ICON }).addTo(map);
}

export function initLeafletMaps() {
  document.querySelectorAll("[data-map-leaflet]").forEach(initMap);
}

/* Alpine компонент: интерактивная мини-карта в backoffice для ContactsPage edit.
 *
 * Реактивно следит за изменением полей latitude/longitude/map_zoom внутри формы
 * (data-form-id), пересоздаёт маркер и пан/зум при каждом изменении (debounce
 * 200ms). Если хотя бы одна координата пуста — карта скрывается, виден
 * placeholder. Те же тайлы/иконка, что на публичной странице (стиль идентичен).
 */
export function boMapPreview() {
  return {
    map: null,
    marker: null,
    hasCoords: false,
    formId: "",
    _t: null,
    _onChange: null,

    init() {
      const root = this.$root;
      this.formId = root.dataset.formId || "";
      const initialLat = parseFloat(root.dataset.initialLat);
      const initialLng = parseFloat(root.dataset.initialLng);
      const initialZoom = parseInt(root.dataset.initialZoom, 10) || 16;

      this._mountMap(initialLat, initialLng, initialZoom);

      // Слушаем input/change на полях формы. Debounce 200ms — пока менеджер
      // печатает координаты, не дёргаем карту каждой цифрой.
      const form = document.getElementById(this.formId);
      if (!form) return;
      this._onChange = (e) => {
        const name = e.target.name || "";
        if (name !== "latitude" && name !== "longitude" && name !== "map_zoom") return;
        clearTimeout(this._t);
        this._t = setTimeout(() => this._sync(), 200);
      };
      form.addEventListener("input", this._onChange);
      form.addEventListener("change", this._onChange);
    },

    destroy() {
      const form = document.getElementById(this.formId);
      if (form && this._onChange) {
        form.removeEventListener("input", this._onChange);
        form.removeEventListener("change", this._onChange);
      }
      if (this._ro) {
        this._ro.disconnect();
        this._ro = null;
      }
      if (this.map) {
        this.map.remove();
        this.map = null;
      }
    },

    _readCoords() {
      const form = document.getElementById(this.formId);
      if (!form) return { lat: NaN, lng: NaN, zoom: 16 };
      const lat = parseFloat(form.querySelector('[name="latitude"]')?.value);
      const lng = parseFloat(form.querySelector('[name="longitude"]')?.value);
      const zoom = parseInt(form.querySelector('[name="map_zoom"]')?.value, 10) || 16;
      return { lat, lng, zoom };
    },

    /* Записать lat/lng в форму после клика/drag по карте. 6 знаков после
     * точки = ~10 см precision (так же как в ContactsPage.coordinates property).
     * Двигаем маркер сразу (видимый отклик), inputs триггерят `input` event —
     * stepper и наш _sync через 200ms заметят, но setView с тем же значением
     * визуально не изменит ничего → цикла нет. */
    _writeLatLng(latlng) {
      const form = document.getElementById(this.formId);
      if (!form) return;
      const lat = latlng.lat.toFixed(6);
      const lng = latlng.lng.toFixed(6);
      const latEl = form.querySelector('[name="latitude"]');
      const lngEl = form.querySelector('[name="longitude"]');
      if (latEl) {
        latEl.value = lat;
        latEl.dispatchEvent(new Event("input", { bubbles: true }));
        latEl.dispatchEvent(new Event("change", { bubbles: true }));
      }
      if (lngEl) {
        lngEl.value = lng;
        lngEl.dispatchEvent(new Event("input", { bubbles: true }));
        lngEl.dispatchEvent(new Event("change", { bubbles: true }));
      }
      if (this.marker) this.marker.setLatLng(latlng);
    },

    _writeZoom(z) {
      const form = document.getElementById(this.formId);
      if (!form) return;
      const zoomEl = form.querySelector('[name="map_zoom"]');
      if (!zoomEl) return;
      const current = parseInt(zoomEl.value, 10);
      if (current === z) return;
      zoomEl.value = String(z);
      zoomEl.dispatchEvent(new Event("input", { bubbles: true }));
      zoomEl.dispatchEvent(new Event("change", { bubbles: true }));
    },

    _mountMap(lat, lng, zoom) {
      const el = this.$refs.map;
      if (!el) return;
      const isValid = !Number.isNaN(lat) && !Number.isNaN(lng);
      this.hasCoords = isValid;
      if (!isValid) return;

      // Откладываем init Leaflet'а до тех пор, пока контейнер действительно
      // получит размер. В Alpine init() контейнер может быть 0×0 (CSS
      // aspect-ratio ещё не пересчитан), и L.map в нулевом контейнере
      // не запросит ни одного тайла — карта останется пустой. Опрашиваем
      // через rAF до первого ненулевого clientHeight (макс 30 кадров ≈ 500ms).
      const tryMount = (attemptsLeft) => {
        if (!el.isConnected) return;
        if (el.clientWidth > 0 && el.clientHeight > 0) {
          this._actuallyMount(el, lat, lng, zoom);
          return;
        }
        if (attemptsLeft <= 0) {
          // Сдаёмся и монтируем как есть — invalidateSize и ResizeObserver
          // ниже подтянут тайлы как только размер появится.
          this._actuallyMount(el, lat, lng, zoom);
          return;
        }
        requestAnimationFrame(() => tryMount(attemptsLeft - 1));
      };
      tryMount(30);
    },

    _actuallyMount(el, lat, lng, zoom) {
      this.map = L.map(el, {
        center: [lat, lng],
        zoom,
        scrollWheelZoom: false,
        zoomControl: true,
        attributionControl: false,
      });
      L.tileLayer(TILE_URL, { maxZoom: 19 }).addTo(this.map);
      this.marker = L.marker([lat, lng], { icon: MARKER_ICON, draggable: true }).addTo(this.map);

      // Клик по карте → переставить маркер и записать координаты в форму.
      this.map.on("click", (ev) => this._writeLatLng(ev.latlng));
      // Drag end маркера → то же самое (Leaflet даёт finalLatLng в event.target).
      this.marker.on("dragend", (ev) => this._writeLatLng(ev.target.getLatLng()));
      // Zoom-кнопки → записать новый zoom в поле map_zoom.
      this.map.on("zoomend", () => this._writeZoom(this.map.getZoom()));

      // Дополнительная страховка: invalidateSize после первого paint —
      // если контейнер за время tryMount всё-таки не успел получить
      // финальный размер, эта итерация догонит. ResizeObserver ловит
      // последующие resize'ы (sidebar toggle, mobile rotation, открытие
      // соседних accordion-панелей).
      requestAnimationFrame(() => {
        if (this.map) this.map.invalidateSize();
      });
      if (typeof ResizeObserver !== "undefined") {
        this._ro = new ResizeObserver(() => {
          if (this.map) this.map.invalidateSize();
        });
        this._ro.observe(el);
      }
    },

    _sync() {
      const { lat, lng, zoom } = this._readCoords();
      const isValid = !Number.isNaN(lat) && !Number.isNaN(lng);

      if (!isValid) {
        this.hasCoords = false;
        if (this._ro) {
          this._ro.disconnect();
          this._ro = null;
        }
        if (this.map) {
          this.map.remove();
          this.map = null;
          this.marker = null;
        }
        return;
      }

      // Координаты появились впервые — создаём карту.
      if (!this.map) {
        this._mountMap(lat, lng, zoom);
        return;
      }

      // Обновляем существующую карту.
      this.hasCoords = true;
      this.map.setView([lat, lng], zoom);
      if (this.marker) {
        this.marker.setLatLng([lat, lng]);
      } else {
        this.marker = L.marker([lat, lng], { icon: MARKER_ICON }).addTo(this.map);
      }
    },
  };
}
