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
