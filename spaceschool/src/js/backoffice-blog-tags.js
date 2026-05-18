/* Alpine компонент boTagPicker — выбор тегов для BlogPost edit.
 *
 * Сценарий:
 * 1. На странице есть hidden input `tags_json` внутри основной формы
 *    (имя и form-id передаются через data-атрибуты).
 * 2. Компонент рендерит 3 секции badge-чипов:
 *      - Выбранные (можно кликнуть → удалить)
 *      - Доступные (теги региона, ещё не выбранные — клик добавляет)
 *      - Предложенные AI (после клика на «Подобрать через AI»)
 * 3. Кастомные теги через input «+ Добавить» с авто-slug из транслитерации.
 * 4. На каждое изменение selected/customNames — обновляется значение
 *    скрытого input'а формы. View парсит JSON и синкает M2M.
 *
 * Использование в шаблоне:
 *   <div x-data="boTagPicker"
 *        data-suggest-url="..."
 *        data-form-id="blog-edit-form"
 *        data-hidden-name="tags_json"
 *        data-initial='[{"slug":"...","name":"..."}]'
 *        data-all-tags='[{"pk":1,"slug":"...","name":"..."}]'>...
 */

/** Привести payload тега к каноническому виду {slug, name, names:{ru,kk,en}}. */
function normalizeTag(t) {
  if (!t) return { slug: "", name: "", names: { ru: "", kk: "", en: "" } };
  const names = t.names && typeof t.names === "object" ? t.names : {};
  const ru = (names.ru || "").trim() || (t.name || "").trim();
  return {
    slug: t.slug || "",
    name: t.name || ru || "",
    names: {
      ru: ru,
      kk: (names.kk || "").trim(),
      en: (names.en || "").trim(),
    },
    is_new: t.is_new || false,
  };
}

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[2]) : "";
}

// Простая транслитерация рус → латиница + kebab-case (для авто-slug кастомных).
const TRANSLIT_MAP = {
  а: "a", б: "b", в: "v", г: "g", д: "d", е: "e", ё: "yo", ж: "zh",
  з: "z", и: "i", й: "y", к: "k", л: "l", м: "m", н: "n", о: "o",
  п: "p", р: "r", с: "s", т: "t", у: "u", ф: "f", х: "h", ц: "ts",
  ч: "ch", ш: "sh", щ: "sch", ъ: "", ы: "y", ь: "", э: "e", ю: "yu",
  я: "ya",
};

function toSlug(text) {
  const lower = (text || "").toLowerCase().trim();
  const transliterated = lower
    .split("")
    .map((ch) => (TRANSLIT_MAP[ch] !== undefined ? TRANSLIT_MAP[ch] : ch))
    .join("");
  return transliterated
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
}

function boTagPicker() {
  return {
    suggestUrl: "",
    formId: "",
    hiddenName: "tags_json",
    /** Все теги: [{slug, name, names: {ru, kk, en}}] */
    allTags: [],
    /** Выбранные теги (в M2M): [{slug, name, names: {ru, kk, en}}] */
    selected: [],
    /** Кастомное имя для нового тега (то что пользователь печатает в input) */
    customName: "",
    /** Предложенные AI: [{slug, name, names, is_new}] */
    suggested: [],
    loading: false,
    status: "",
    error: "",
    /** Текущий язык (sync с родительским lang таб-баром через x-effect). */
    currentLang: "ru",

    /** Hidden-input основной формы для tags_json. */
    _hiddenInput: null,

    init() {
      const root = this.$root;
      this.suggestUrl = root.dataset.suggestUrl || "";
      this.formId = root.dataset.formId || "";
      this.hiddenName = root.dataset.hiddenName || "tags_json";

      try {
        this.selected = (JSON.parse(root.dataset.initial || "[]") || []).map(normalizeTag);
      } catch (e) {
        this.selected = [];
      }
      try {
        this.allTags = (JSON.parse(root.dataset.allTags || "[]") || []).map(normalizeTag);
      } catch (e) {
        this.allTags = [];
      }

      // Найти hidden input в форме — поддерживаем form.elements (включая
      // поля привязанные через HTML5 form= атрибут).
      const form = document.getElementById(this.formId);
      if (form) {
        this._hiddenInput =
          form.elements[this.hiddenName] ||
          form.querySelector(`input[name="${CSS.escape(this.hiddenName)}"]`);
      }
      this.syncHidden();
    },

    /** Sync currentLang с родительским tab-bar. Вызывается через x-effect в шаблоне. */
    syncLang(lang) {
      if (lang && lang !== this.currentLang) {
        this.currentLang = lang;
      }
    },

    /** Имя тега на текущем языке с fallback'ом на RU и на base name. */
    displayName(t) {
      if (!t) return "";
      const names = t.names || {};
      return (names[this.currentLang] || names.ru || t.name || "").trim();
    },

    /** Список доступных = allTags минус selected (по slug). Сортировка — по
     * имени на текущем языке (с fallback'ом). */
    get availableSorted() {
      const selectedSlugs = new Set(this.selected.map((t) => t.slug));
      const lang = this.currentLang;
      return this.allTags
        .filter((t) => !selectedSlugs.has(t.slug))
        .slice()
        .sort((a, b) => this.displayName(a).localeCompare(this.displayName(b), lang || "ru"));
    },

    /** Сериализовать выбранные теги в JSON для hidden input. */
    serialized() {
      return JSON.stringify(
        this.selected.map((t) => ({
          slug: t.slug,
          name: t.name || (t.names && t.names.ru) || "",
          names: t.names || { ru: t.name || "", kk: "", en: "" },
        })),
      );
    },

    /** Записать сериализованное значение в hidden input + dispatch change для stepper. */
    syncHidden() {
      if (!this._hiddenInput) return;
      this._hiddenInput.value = this.serialized();
      this._hiddenInput.dispatchEvent(new Event("input", { bubbles: true }));
      this._hiddenInput.dispatchEvent(new Event("change", { bubbles: true }));
    },

    select(tag) {
      if (this.selected.some((t) => t.slug === tag.slug)) return;
      this.selected.push(normalizeTag(tag));
      this.syncHidden();
    },

    remove(idx) {
      this.selected.splice(idx, 1);
      this.syncHidden();
    },

    addCustom() {
      const name = (this.customName || "").trim();
      if (!name) return;
      const slug = toSlug(name);
      if (!slug) {
        this.error = "Не удалось сгенерировать slug для этого названия — используй латиницу.";
        return;
      }
      this.error = "";
      // Если такой slug уже есть в allTags — выбираем существующий вместо дубля.
      const existing = this.allTags.find((t) => t.slug === slug);
      if (existing) {
        this.select(existing);
      } else if (!this.selected.some((t) => t.slug === slug)) {
        // Имя кладём на текущий язык; остальные пустые (будут переведены через
        // Авто-перевод тегов на taxonomy странице или менеджером вручную).
        const names = { ru: "", kk: "", en: "" };
        names[this.currentLang] = name;
        if (!names.ru) names.ru = name; // RU должен быть всегда, base в БД
        this.selected.push({ slug, name, names });
        this.syncHidden();
      }
      this.customName = "";
    },

    acceptSuggestion(tag) {
      this.select(tag);
      this.suggested = this.suggested.filter((t) => t.slug !== tag.slug);
    },

    dismissAll() {
      this.suggested = [];
      this.status = "";
    },

    /** Собрать RU контент текущей формы и попросить Gemini подобрать теги. */
    async suggest() {
      if (this.loading) return;
      this.error = "";
      this.status = "";

      const form = document.getElementById(this.formId);
      if (!form) {
        this.error = "Форма не найдена.";
        return;
      }

      const titleEl = form.elements["title_ru"];
      const leadEl = form.elements["lead_ru"];
      const contentEl = form.elements["content_ru"];
      const title = (titleEl && titleEl.value) || "";
      const lead = (leadEl && leadEl.value) || "";
      const content = (contentEl && contentEl.value) || "";

      if (!title.trim() && !lead.trim() && !content.trim()) {
        this.error = "Заполни заголовок и хотя бы лид/контент на RU.";
        return;
      }

      this.loading = true;
      this.status = "Gemini подбирает теги…";

      try {
        const res = await fetch(this.suggestUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          credentials: "same-origin",
          body: JSON.stringify({ title, lead, content }),
        });

        if (!res.ok) {
          let detail = "";
          try {
            const data = await res.json();
            detail = data.error || JSON.stringify(data);
          } catch (e) {
            detail = await res.text();
          }
          throw new Error(`${res.status}: ${detail.slice(0, 300)}`);
        }

        const data = await res.json();
        const tags = data.tags || [];
        // Фильтруем те, что уже выбраны
        const selectedSlugs = new Set(this.selected.map((t) => t.slug));
        this.suggested = tags.filter((t) => !selectedSlugs.has(t.slug));

        if (this.suggested.length === 0) {
          this.status = "AI не нашёл подходящих тегов или все уже выбраны.";
        } else {
          this.status = `Готово: ${this.suggested.length} предложений. Кликни на тег чтобы принять.`;
        }
      } catch (e) {
        this.error = String(e.message || e);
        this.status = "";
      } finally {
        this.loading = false;
      }
    },
  };
}

export function registerBackofficeBlogTags(Alpine) {
  Alpine.data("boTagPicker", boTagPicker);
}
