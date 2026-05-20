/* Alpine компонент авто-перевода translatable полей в backoffice (Gemini).
 *
 * Сценарий:
 * 1. На странице edit (например HomePage) есть пары инпутов <name>_ru / <name>_kk / <name>_en.
 * 2. Менеджер жмёт «Авто-перевод» в footer.
 * 3. Компонент собирает: для каждого base — если KK или EN инпут пустой и RU непустой,
 *    он попадает в payload для соответствующего языка.
 * 4. POST на сервер. Сервер дёргает Gemini, возвращает {translations: {kk:{...}, en:{...}}}.
 * 5. Компонент заполняет соответствующие инпуты + dispatch input event — чтобы stepper
 *    пересчитал completeness.
 * 6. Менеджер видит переводы, может править, и сабмитит общую форму сам.
 *
 * Использование в шаблоне:
 *   <div x-data="boAutoTranslate"
 *        data-url="{% url 'backoffice:content_home_translate' pk=home.pk %}"
 *        data-form-id="home-edit-form"
 *        data-bases-json='[...JSON list of base field names...]'>
 *     <button @click="run()" :disabled="loading">...</button>
 *     <span x-text="status"></span>
 *   </div>
 */

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[2]) : "";
}

/* Опции на компонент:
 * - data-url, data-form-id — обязательные.
 * - data-bases-json — список base полей (статичный режим, scope = главная форма + опц. prefix).
 * - data-prefix — префикс для inline-formset (статичный режим), напр. "departments-0-".
 * - data-scan-form="1" — авто-режим: компонент сам сканирует форму и находит ВСЕ
 *   `<prefix><base>_ru` инпуты (включая inline-formset карточки типа audience_items-0-title_ru).
 *   В этом режиме data-bases-json и data-prefix игнорируются. Используется для глобальной
 *   кнопки «Авто-перевод» в табах языков — чтобы карточки inline-formset'а тоже попадали в перевод.
 * - data-force="1" — перетирать непустые KK/EN. Требует confirm() если хоть
 *   одно KK/EN было заполнено. Без force заполняются только пустые. */
function boAutoTranslate() {
  return {
    url: "",
    formId: "",
    bases: [],
    prefix: "",
    force: false,
    scanForm: false,
    loading: false,
    status: "",
    error: "",

    init() {
      const root = this.$root;
      this.url = root.dataset.url || "";
      this.formId = root.dataset.formId || "";
      this.prefix = root.dataset.prefix || "";  // для inline-formset, напр. "departments-0-"
      this.force = root.dataset.force === "1" || root.dataset.force === "true";
      this.scanForm = root.dataset.scanForm === "1" || root.dataset.scanForm === "true";
      try {
        this.bases = JSON.parse(root.dataset.basesJson || "[]");
      } catch (e) {
        this.bases = [];
      }
    },

    _form() {
      return document.getElementById(this.formId);
    },

    _inputByName(name) {
      const form = this._form();
      if (!form) return null;
      // form.elements включает поля, привязанные к форме через HTML5
      // form="..." атрибут, даже если они лежат вне DOM-tree <form>.
      // SEO-блок и og_image в edit-страницах рендерятся ВНЕ <form>
      // (после inline-formset), поэтому querySelector внутри form не нашёл бы их.
      return form.elements[name] || form.querySelector(`[name="${CSS.escape(name)}"]`);
    },

    /* Возвращает список {prefix, base} для перевода.
     * Статический режим: декартово произведение this.prefix × this.bases.
     * Scan-режим: ищем в форме все `<prefix><base>_ru` инпуты — включая inline-formset
     *   (audience_items-0-title_ru), у которых есть пара `_kk` или `_en`. */
    _pairs() {
      if (!this.scanForm) {
        return this.bases.map(base => ({ prefix: this.prefix, base }));
      }
      const form = this._form();
      if (!form) return [];
      // Django formset name: `<formset>-<index>-<field>` (например audience_items-0-title).
      // Главная форма: просто `<field>` без `-N-`. Этим regex отделяем formset-prefix.
      const FORMSET_RE = /^(.*-\d+-)([^-]+)$/;
      const out = [];
      const seen = new Set();
      for (const el of form.elements) {
        const name = el.name || "";
        if (!name.endsWith("_ru")) continue;
        const stem = name.slice(0, -3);
        let prefix, base;
        const m = stem.match(FORMSET_RE);
        if (m) {
          prefix = m[1];
          base = m[2];
        } else {
          prefix = "";
          base = stem;
        }
        const key = `${prefix}|${base}`;
        if (seen.has(key)) continue;
        // Игнорим случайные `_ru` имена без translation-пары (`_kk` или `_en`).
        const kk = form.elements[`${prefix}${base}_kk`];
        const en = form.elements[`${prefix}${base}_en`];
        if (!kk && !en) continue;
        seen.add(key);
        out.push({ prefix, base });
      }
      return out;
    },

    /* Собираем payload для сервера.
     * Без force — пропускаем пары, где KK/EN уже заполнен.
     * С force — отправляем ВСЕ пары, где есть RU (заполненные KK/EN перетрутся). */
    collect() {
      const payload = { kk: {}, en: {} };
      let pending = 0;
      let willOverwrite = 0;
      for (const { prefix, base } of this._pairs()) {
        const ru = this._inputByName(`${prefix}${base}_ru`);
        if (!ru) continue;
        const ruValue = (ru.value || "").trim();
        if (!ruValue) continue;
        for (const lang of ["kk", "en"]) {
          const target = this._inputByName(`${prefix}${base}_${lang}`);
          if (!target) continue;
          const targetValue = (target.value || "").trim();
          if (targetValue && !this.force) continue;
          if (targetValue) willOverwrite += 1;
          // serverKey включает prefix — при возврате с сервера можно найти инпут напрямую.
          payload[lang][`${prefix}${base}`] = ru.value;
          pending += 1;
        }
      }
      return { payload, pending, willOverwrite };
    },

    async run() {
      if (this.loading) return;
      this.error = "";
      this.status = "";

      const { payload, pending, willOverwrite } = this.collect();
      if (pending === 0) {
        this.status = this.force
          ? "Нет RU-контента в этом блоке — нечего переводить."
          : "Все KK/EN поля уже заполнены — нечего переводить.";
        return;
      }

      if (this.force && willOverwrite > 0) {
        const ok = confirm(
          `Перевести блок принудительно? ${willOverwrite} уже заполненных KK/EN полей будут перезаписаны.`
        );
        if (!ok) return;
      }

      this.loading = true;
      this.status = `Перевод ${pending} полей через Gemini…`;

      try {
        const res = await fetch(this.url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          credentials: "same-origin",
          body: JSON.stringify({ by_lang: payload }),
        });

        const raw = await res.text();
        let data;
        try {
          data = raw ? JSON.parse(raw) : {};
        } catch (e) {
          data = null;
        }

        if (!res.ok) {
          const detail = (data && (data.error || JSON.stringify(data))) || raw;
          throw new Error(`${res.status}: ${(detail || "").slice(0, 300)}`);
        }

        const translations = (data && data.translations) || {};
        let filled = 0;

        for (const lang of ["kk", "en"]) {
          const fields = translations[lang] || {};
          for (const [serverKey, text] of Object.entries(fields)) {
            // serverKey == `<prefix><base>` — ищем инпут по имени напрямую,
            // одинаково работает и для главной формы, и для inline-formset.
            const input = this._inputByName(`${serverKey}_${lang}`);
            if (!input) continue;
            if (!this.force && (input.value || "").trim()) continue;
            input.value = text;
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
            filled += 1;
          }
        }

        this.status = filled
          ? `Готово: заполнено ${filled} полей. Проверь и сохрани.`
          : "Gemini не вернул переводы.";
      } catch (e) {
        this.error = String(e.message || e);
        this.status = "";
      } finally {
        this.loading = false;
      }
    },
  };
}

/* Alpine компонент авто-генерации SEO/OG-полей через Gemini.
 *
 * Сценарий:
 * 1. На edit-странице есть seo_title_<lang>, seo_description_<lang>,
 *    og_title_<lang>, og_description_<lang> инпуты во всех 3 языках (12 шт).
 * 2. Источник для генерации — контент страницы на RU (hero_title_ru, и т.д.),
 *    список передаётся через data-source-fields (CSV).
 * 3. Менеджер жмёт «Авто-генерация SEO».
 * 4. Компонент собирает RU контент → POST → Gemini → ответ {seo:{lang:{field:text}}}.
 * 5. Заполняет ТОЛЬКО пустые SEO/OG инпуты (не перетирает работу менеджера).
 * 6. Dispatch input/change → stepper.
 *
 * Использование:
 *   <div x-data="boAutoSEO"
 *        data-url="{% url 'backoffice:content_home_seo' pk=home.pk %}"
 *        data-form-id="home-edit-form"
 *        data-source-fields="hero_title,hero_subtitle,about_title,about_body">
 *     <button @click="run()" :disabled="loading">...</button>
 *   </div>
 */
function boAutoSEO() {
  return {
    url: "",
    formId: "",
    sourceFields: [],
    loading: false,
    status: "",
    error: "",

    SEO_FIELDS: ["seo_title", "seo_description", "og_title", "og_description"],
    LANGS: ["ru", "kk", "en"],

    init() {
      const root = this.$root;
      this.url = root.dataset.url || "";
      this.formId = root.dataset.formId || "";
      this.sourceFields = (root.dataset.sourceFields || "")
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
    },

    _input(name) {
      const form = document.getElementById(this.formId);
      if (!form) return null;
      // form.elements находит поля, привязанные к форме через HTML5 form= атрибут
      // — SEO/OG поля рендерятся ВНЕ <form>, через form.querySelector их не найти.
      return form.elements[name] || form.querySelector(`[name="${CSS.escape(name)}"]`);
    },

    /* Собираем RU контент. Берём `<base>_ru` для каждого base в sourceFields. */
    collectContent() {
      const content = {};
      for (const base of this.sourceFields) {
        const ru = this._input(`${base}_ru`);
        if (!ru) continue;
        const v = (ru.value || "").trim();
        if (v) content[base] = ru.value;
      }
      return content;
    },

    async run() {
      if (this.loading) return;
      this.error = "";
      this.status = "";

      const content = this.collectContent();
      if (Object.keys(content).length === 0) {
        this.error = "Нет RU-контента (hero/about). Заполни сначала русский, потом сгенерируй SEO.";
        return;
      }

      this.loading = true;
      this.status = "Генерируем SEO/OG через Gemini…";

      try {
        const res = await fetch(this.url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          credentials: "same-origin",
          body: JSON.stringify({ content }),
        });

        const raw = await res.text();
        let data;
        try {
          data = raw ? JSON.parse(raw) : {};
        } catch (e) {
          data = null;
        }

        if (!res.ok) {
          const detail = (data && (data.error || JSON.stringify(data))) || raw;
          throw new Error(`${res.status}: ${(detail || "").slice(0, 300)}`);
        }

        const seo = (data && data.seo) || {};
        let filled = 0;

        for (const lang of this.LANGS) {
          const fields = seo[lang] || {};
          for (const field of this.SEO_FIELDS) {
            const text = fields[field];
            if (!text) continue;
            const input = this._input(`${field}_${lang}`);
            if (!input) continue;
            if ((input.value || "").trim()) continue;  // не перетираем
            input.value = text;
            input.dispatchEvent(new Event("input", { bubbles: true }));
            input.dispatchEvent(new Event("change", { bubbles: true }));
            filled += 1;
          }
        }

        this.status = filled
          ? `Готово: заполнено ${filled} полей. Проверь и сохрани.`
          : "Все SEO/OG поля уже заполнены — нечего обновлять.";
      } catch (e) {
        this.error = String(e.message || e);
        this.status = "";
      } finally {
        this.loading = false;
      }
    },
  };
}

export function registerBackofficeTranslate(Alpine) {
  Alpine.data("boAutoTranslate", boAutoTranslate);
  Alpine.data("boAutoSEO", boAutoSEO);
}
