/* Alpine компонент для backoffice галереи главной.
 *
 * UX:
 * 1. Drop zone: drag-and-drop файлов из ОС → POST /upload/ → карточки появляются
 * 2. Click button «Загрузить» — стандартный multi-file picker → POST /upload/
 * 3. Drag-сортировка карточек через SortableJS → POST /reorder/
 * 4. Click ✕ — DELETE /<pk>/
 * 5. Edit alt-text inline — POST /<pk>/ (PATCH-style)
 *
 * Все endpoints возвращают JSON. CSRF берётся из cookie csrftoken.
 *
 * Logic warning «не подходящий слот»: позиция i рассчитывает «ожидаемую»
 * ориентацию через расчёт по zip-алгоритму. Если orientation картинки
 * не совпадает с ожидаемой — рисуется ⚠ badge.
 */
import Sortable from "sortablejs";

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[2]) : "";
}

async function postJSON(url, body, { isForm = false } = {}) {
  const headers = { "X-CSRFToken": getCookie("csrftoken") };
  if (!isForm) headers["Content-Type"] = "application/json";
  const res = await fetch(url, {
    method: "POST",
    headers,
    body: isForm ? body : JSON.stringify(body),
    credentials: "same-origin",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text.slice(0, 200)}`);
  }
  return res.json();
}

/* Рассчитать «ожидаемую» ориентацию для позиции i, основываясь на
 * том, что мы по zip-алгоритму ставим wide на чётные slot-индексы
 * (0,2,4,...) и tall на нечётные (1,3,5,...). square не warning-ит. */
function expectedAt(index) {
  return index % 2 === 0 ? "wide" : "tall";
}

/* Alpine компонент для preview видео-файла.
 * Считывает HTML5 metadata (videoWidth × videoHeight, duration) после
 * loadedmetadata. Также проверяет размер выбранного файла перед submit'ом
 * формы (client-side soft check на лимит 35MB). */
function boVideoPreview() {
  return {
    dims: "",
    dur: "",
    error: "",
    picking: "",
    MAX_BYTES: 35 * 1024 * 1024,

    init() {
      // На стартовой загрузке плеер сам стриггерит loadedmetadata
    },

    onMeta(ev) {
      const v = ev.target;
      if (v.videoWidth && v.videoHeight) {
        this.dims = `${v.videoWidth}×${v.videoHeight}`;
      }
      if (Number.isFinite(v.duration)) {
        const s = Math.round(v.duration);
        const mm = Math.floor(s / 60);
        const ss = (s % 60).toString().padStart(2, "0");
        this.dur = `${mm}:${ss}`;
      }
    },

    onPick(ev) {
      this.error = "";
      this.picking = "";
      const f = ev.target.files && ev.target.files[0];
      if (!f) return;
      if (f.size > this.MAX_BYTES) {
        const mb = (f.size / 1024 / 1024).toFixed(1);
        this.error =
          `Файл ${mb} MB слишком большой (лимит 35 MB). Сожми через HandBrake ` +
          "(preset Web-Optimized, bitrate ~3 Mbps) или CloudConvert — обычно " +
          "20–40-сек 1080p ролик умещается в 20–30 MB без видимой потери качества.";
        ev.target.value = "";
        return;
      }
      const mb = (f.size / 1024 / 1024).toFixed(1);
      this.picking = `Выбрано: ${f.name} (${mb} MB) — нажми «Сохранить» внизу`;
    },
  };
}

/* Stepper заполнения формы (backoffice/content/home/edit).
 *
 * Получает список шагов с server-side initial state. Слушает input/change
 * events на форме и пересчитывает filled count для каждого шага.
 * Save кнопка disabled пока обязательный шаг не complete.
 *
 * Файл-инпуты считаются "filled" если либо был сохранён файл на сервере
 * (initial[name] === true), либо менеджер выбрал новый (files.length > 0).
 */
function boFormSteps() {
  return {
    steps: [],
    formId: "",
    form: null,
    fieldFilled: {},  // {name: bool} — текущее состояние всех tracked полей
    _recomputeTimer: null,

    init() {
      const root = this.$root;
      this.formId = root.dataset.formId;
      try {
        this.steps = JSON.parse(root.dataset.stepsJson || "[]");
      } catch (e) {
        return;
      }
      // Поднимем initial state из server в локальный кэш
      this.fieldFilled = {};
      for (const step of this.steps) {
        for (const [name, v] of Object.entries(step.initial || {})) {
          this.fieldFilled[name] = v;
        }
      }
      this.form = document.getElementById(this.formId);
      // Слушаем document, не form: некоторые tracked поля (SEO/og_image) лежат
      // ВНЕ form-tag и связаны с формой через HTML5 form="..." атрибут — события
      // от них до <form> не bubble'ятся. Фильтр по name in fieldFilled оставляет
      // только нужные.
      document.addEventListener("input", (e) => this.onFieldChange(e, true));
      document.addEventListener("change", (e) => this.onFieldChange(e, false));
      this.recompute();
    },

    onFieldChange(ev, debounced) {
      const el = ev.target;
      if (!el.name) return;
      if (!(el.name in this.fieldFilled)) return;  // не отслеживаем
      if (el.type === "file") {
        const wasOnServer = this.steps
          .flatMap(s => Object.entries(s.initial || {}))
          .find(([n, v]) => n === el.name && v);
        this.fieldFilled[el.name] = el.files.length > 0 || !!wasOnServer;
      } else {
        this.fieldFilled[el.name] = (el.value || "").trim() !== "";
      }
      if (debounced) {
        clearTimeout(this._recomputeTimer);
        this._recomputeTimer = setTimeout(() => this.recompute(), 150);
      } else {
        this.recompute();
      }
    },

    recompute() {
      this.steps = this.steps.map(step => {
        // readonly шаги (departments) считают на сервере при загрузке и не
        // пересчитываются в JS — у них fields пустой.
        if (step.readonly) {
          return { ...step, complete: step.filled === step.total };
        }
        const filled = step.fields.filter(n => this.fieldFilled[n]).length;
        return { ...step, filled, complete: filled === step.total };
      });
    },

    stepClass(step) {
      if (step.complete) return "bo-step-complete";
      if (step.required && step.filled < step.total) return "bo-step-required-empty";
      if (step.filled > 0) return "bo-step-partial";
      return "bo-step-empty";
    },

    get canSave() {
      return this.steps.every(s => !s.required || s.complete);
    },

    get blockedReason() {
      const blocked = this.steps.find(s => s.required && !s.complete);
      if (!blocked) return "";
      return `Заполни обязательный шаг «${blocked.label}» (${blocked.filled}/${blocked.total})`;
    },
  };
}

/* Blog gallery — упрощённый компонент без orientation/strict-zip-warning.
 * Поля для inline edit: alt + caption (на 3 языках). Сортировка через SortableJS. */
function boBlogGallery() {
  return {
    items: [],
    uploadUrl: "",
    reorderUrl: "",
    updateUrlTemplate: "",
    deleteUrlTemplate: "",
    dragging: false,
    uploading: false,
    error: "",
    /** Sync currentLang с родительским tab-bar — те же inputs alt/caption переключаются. */
    currentLang: "ru",

    init() {
      const root = this.$root;
      this.uploadUrl = root.dataset.uploadUrl || "";
      this.reorderUrl = root.dataset.reorderUrl || "";
      this.updateUrlTemplate = root.dataset.updateUrlTemplate || "";
      this.deleteUrlTemplate = root.dataset.deleteUrlTemplate || "";

      const itemsScriptId = root.dataset.itemsScript;
      if (itemsScriptId) {
        const el = document.getElementById(itemsScriptId);
        if (el) {
          try { this.items = JSON.parse(el.textContent || "[]"); }
          catch (e) { this.error = "Не удалось разобрать данные галереи"; }
        }
      }

      this.$nextTick(() => {
        Sortable.create(this.$refs.grid, {
          animation: 150,
          handle: ".bo-gallery-card-drag",
          ghostClass: "bo-gallery-card-ghost",
          onEnd: () => this.persistOrder(),
        });
      });
    },

    syncLang(lang) {
      if (lang && lang !== this.currentLang) this.currentLang = lang;
    },

    async handleFiles(fileList) {
      if (!fileList || !fileList.length) return;
      const files = Array.from(fileList).filter(f => f.type.startsWith("image/"));
      if (!files.length) return;

      this.uploading = true;
      this.error = "";
      const fd = new FormData();
      for (const f of files) fd.append("images", f);

      try {
        const data = await postJSON(this.uploadUrl, fd, { isForm: true });
        this.items = data.items;
      } catch (e) {
        this.error = String(e.message || e);
      } finally {
        this.uploading = false;
      }
    },

    onDrop(event) {
      this.dragging = false;
      this.handleFiles(event.dataTransfer.files);
    },

    onPick(event) {
      this.handleFiles(event.target.files);
      event.target.value = "";
    },

    async persistOrder() {
      const newOrder = Array.from(this.$refs.grid.children)
        .map((el) => parseInt(el.dataset.pk, 10))
        .filter(Boolean);
      this.items.sort((a, b) => newOrder.indexOf(a.pk) - newOrder.indexOf(b.pk));
      try {
        await postJSON(this.reorderUrl, { order: newOrder });
      } catch (e) {
        this.error = String(e.message || e);
      }
    },

    async remove(item) {
      if (!confirm("Удалить картинку из галереи?")) return;
      try {
        await postJSON(this.deleteUrlTemplate.replace("0", item.pk), {});
        this.items = this.items.filter(i => i.pk !== item.pk);
      } catch (e) {
        this.error = String(e.message || e);
      }
    },

    /** Сохранить alt/caption для конкретной картинки (debounced на blur). */
    async saveMeta(item) {
      try {
        await postJSON(this.updateUrlTemplate.replace("0", item.pk), {
          alt_ru: item.alt_ru || "",
          alt_kk: item.alt_kk || "",
          alt_en: item.alt_en || "",
          caption_ru: item.caption_ru || "",
          caption_kk: item.caption_kk || "",
          caption_en: item.caption_en || "",
        });
      } catch (e) {
        this.error = String(e.message || e);
      }
    },
  };
}

/* Backoffice — управление фото внутри ОДНОГО альбома (edit-страница альбома).
 *
 * Компонент работает на странице /backoffice/content/gallery/<album_pk>/.
 * Альбом задаёт region/category на серверной стороне — JS не передаёт их в
 * upload. Фото внутри альбома: bulk-upload, inline toggle is_wide/is_published,
 * inline edit alt, delete. Сортировка — по `-created_at` (без DnD: новые
 * автоматически сверху).
 *
 * `is_wide` ставится auto на upload (PIL по aspect ratio на сервере); кнопка
 * на карточке — ручной override (если автодетект ошибся). */
function boAlbumPhotos() {
  return {
    photos: [],
    uploadUrl: "",
    toggleUrlTemplate: "",
    updateUrlTemplate: "",
    deleteUrlTemplate: "",
    dragging: false,
    uploading: false,
    error: "",
    lang: "ru",

    init() {
      const root = this.$root;
      this.uploadUrl = root.dataset.uploadUrl || "";
      this.toggleUrlTemplate = root.dataset.toggleUrlTemplate || "";
      this.updateUrlTemplate = root.dataset.updateUrlTemplate || "";
      this.deleteUrlTemplate = root.dataset.deleteUrlTemplate || "";

      const photosScriptId = root.dataset.photosScript;
      if (photosScriptId) {
        const el = document.getElementById(photosScriptId);
        if (el) {
          try { this.photos = JSON.parse(el.textContent || "[]"); }
          catch (e) { this.error = "Не удалось разобрать данные фото"; }
        }
      }

      // Подхватываем lang из родительского tab-bar (x-data="{ lang: 'ru' }")
      this.$watch("$parent.lang", (v) => { if (v) this.lang = v; });
      if (this.$el.parentElement?.parentElement?._x_dataStack) {
        // best-effort initial sync
        const parentStack = this.$el.parentElement.parentElement._x_dataStack;
        const parentData = parentStack && parentStack[0];
        if (parentData && parentData.lang) this.lang = parentData.lang;
      }
    },

    async handleFiles(fileList) {
      if (!fileList || !fileList.length) return;
      const files = Array.from(fileList).filter((f) => f.type.startsWith("image/"));
      if (!files.length) {
        this.error = "Только изображения (JPEG/PNG/WebP).";
        return;
      }

      this.uploading = true;
      this.error = "";
      const fd = new FormData();
      for (const f of files) fd.append("images", f);

      try {
        const data = await postJSON(this.uploadUrl, fd, { isForm: true });
        // Prepend новые фото — самое свежее сверху (сортировка как на public).
        this.photos = [...(data.items || []), ...this.photos];
      } catch (e) {
        this.error = String(e.message || e);
      } finally {
        this.uploading = false;
      }
    },

    onDrop(event) {
      this.dragging = false;
      this.handleFiles(event.dataTransfer.files);
    },

    onPick(event) {
      this.handleFiles(event.target.files);
      event.target.value = "";
    },

    async toggleField(item, field) {
      const newValue = !item[field];
      try {
        const data = await postJSON(this.toggleUrlTemplate.replace("0", item.pk), {
          field,
          value: newValue,
        });
        const idx = this.photos.findIndex((i) => i.pk === item.pk);
        if (idx >= 0 && data.item) this.photos[idx] = data.item;
      } catch (e) {
        this.error = String(e.message || e);
      }
    },

    async saveMeta(item) {
      try {
        await postJSON(this.updateUrlTemplate.replace("0", item.pk), {
          alt_ru: item.alt_ru || "",
          alt_kk: item.alt_kk || "",
          alt_en: item.alt_en || "",
          caption_ru: item.caption_ru || "",
          caption_kk: item.caption_kk || "",
          caption_en: item.caption_en || "",
        });
      } catch (e) {
        this.error = String(e.message || e);
      }
    },

    async remove(item) {
      if (!confirm("Удалить фото из альбома?")) return;
      try {
        await postJSON(this.deleteUrlTemplate.replace("0", item.pk), {});
        this.photos = this.photos.filter((i) => i.pk !== item.pk);
      } catch (e) {
        this.error = String(e.message || e);
      }
    },
  };
}


export function registerBackofficeGallery(Alpine) {
  Alpine.data("boVideoPreview", boVideoPreview);
  Alpine.data("boFormSteps", boFormSteps);
  Alpine.data("boBlogGallery", boBlogGallery);
  Alpine.data("boAlbumPhotos", boAlbumPhotos);

  Alpine.data("boGallery", () => ({
    items: [],
    uploadUrl: "",
    reorderUrl: "",
    updateUrlTemplate: "",
    deleteUrlTemplate: "",
    dragging: false,
    uploading: false,
    error: "",

    init() {
      // Конфиг читаем из data-attributes / JSON-script — иначе JSON
      // с кавычками ломает атрибут x-data.
      const root = this.$root;
      this.uploadUrl = root.dataset.uploadUrl || "";
      this.reorderUrl = root.dataset.reorderUrl || "";
      this.updateUrlTemplate = root.dataset.updateUrlTemplate || "";
      this.deleteUrlTemplate = root.dataset.deleteUrlTemplate || "";

      const itemsScriptId = root.dataset.itemsScript;
      if (itemsScriptId) {
        const el = document.getElementById(itemsScriptId);
        if (el) {
          try { this.items = JSON.parse(el.textContent || "[]"); }
          catch (e) { this.error = "Не удалось разобрать данные галереи"; }
        }
      }

      this.$nextTick(() => {
        Sortable.create(this.$refs.grid, {
          animation: 150,
          handle: ".bo-gallery-card-drag",
          ghostClass: "bo-gallery-card-ghost",
          onEnd: () => this.persistOrder(),
        });
      });
    },

    isWarn(index, item) {
      // Square — нейтральная, не warning'им
      if (item.orientation === "square") return false;
      return item.orientation !== expectedAt(index);
    },

    expectedLabel(index) {
      return expectedAt(index) === "wide" ? "широкий" : "высокий";
    },

    async handleFiles(fileList) {
      if (!fileList || !fileList.length) return;
      const files = Array.from(fileList).filter(f => f.type.startsWith("image/"));
      if (!files.length) return;

      this.uploading = true;
      this.error = "";
      const fd = new FormData();
      for (const f of files) fd.append("images", f);

      try {
        const data = await postJSON(this.uploadUrl, fd, { isForm: true });
        // Сервер возвращает {items: [...]} — расставленные по strict-zip позиции
        this.items = data.items;
      } catch (e) {
        this.error = String(e.message || e);
      } finally {
        this.uploading = false;
      }
    },

    onDrop(event) {
      this.dragging = false;
      this.handleFiles(event.dataTransfer.files);
    },

    onPick(event) {
      this.handleFiles(event.target.files);
      event.target.value = "";  // reset для повторного выбора того же файла
    },

    async persistOrder() {
      const newOrder = Array.from(this.$refs.grid.children)
        .map((el) => parseInt(el.dataset.pk, 10))
        .filter(Boolean);
      // Reorder items array локально по новому порядку (без сетевого ответа)
      this.items.sort((a, b) => newOrder.indexOf(a.pk) - newOrder.indexOf(b.pk));
      try {
        await postJSON(this.reorderUrl, { order: newOrder });
      } catch (e) {
        this.error = String(e.message || e);
      }
    },

    async remove(item) {
      if (!confirm("Удалить картинку?")) return;
      try {
        await postJSON(this.deleteUrlTemplate.replace("0", item.pk), {});
        this.items = this.items.filter(i => i.pk !== item.pk);
      } catch (e) {
        this.error = String(e.message || e);
      }
    },

    async saveAlt(item) {
      try {
        await postJSON(this.updateUrlTemplate.replace("0", item.pk), {
          alt_text_ru: item.alt_text_ru || "",
          alt_text_kk: item.alt_text_kk || "",
          alt_text_en: item.alt_text_en || "",
        });
      } catch (e) {
        this.error = String(e.message || e);
      }
    },
  }));
}
