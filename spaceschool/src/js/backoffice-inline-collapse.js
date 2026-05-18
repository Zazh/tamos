import Sortable from "sortablejs";

/**
 * boInlineCollapse / boInlineCollapseCard — collapsible Django inline-formset.
 *
 * Generic для команд/FAQ/любых inline-моделей где менеджеру удобно работать
 * со списком свёрнутых карточек: summary показывает основной заголовок, body
 * раскрывается по клику.
 *
 * Структура DOM:
 *   <div x-data="boInlineCollapse" data-prefix="team_members">
 *     {{ formset.management_form }}
 *     <ul x-ref="list">
 *       {% for f in formset %}<li x-data="boInlineCollapseCard({...})">…</li>{% endfor %}
 *     </ul>
 *     <template x-ref="template">
 *       <li x-data="boInlineCollapseCard({...})">…empty_form с `__prefix__`…</li>
 *     </template>
 *     <button @click="add()">+ Добавить</button>
 *   </div>
 *
 * Параметры карточки (через init args):
 *   initialOpen: bool        — раскрыта ли изначально (true для новых, false для сохранённых)
 *   initialPhoto: string     — URL фото (только для team — для FAQ передаём '')
 *   placeholderLabel: string — что показать в summary когда нет primary-поля
 *   summaryPrimary: string   — base translatable поле для title (e.g. 'name', 'question')
 *   summarySecondary: string — base для subtitle (опц., e.g. 'role')
 *
 * Логика:
 *   - Sortable.create на $refs.list, handle .bo-drag-handle, ghost .bo-collapse-card-ghost.
 *   - add(): клонирует $refs.template.innerHTML, replaceAll '__prefix__' → новый индекс,
 *     инкрементирует TOTAL_FORMS. Alpine auto-инициализирует новый x-data.
 *   - __remove(card): для свежесозданных (без pk) — очищает поля и hide через
 *     .bo-collapse-card-hidden. TOTAL_FORMS не уменьшаем (Django пропустит пустую extra).
 *   - _renumber(): после drag/add записывает индексы в `*-order` hidden inputs.
 */
export function registerBackofficeInlineCollapse(Alpine) {
  Alpine.data("boInlineCollapse", () => ({
    init() {
      this._sortable = Sortable.create(this.$refs.list, {
        animation: 150,
        handle: ".bo-drag-handle",
        ghostClass: "bo-collapse-card-ghost",
        filter: ".bo-collapse-card-hidden",
        onEnd: () => this._renumber(),
      });
    },

    add() {
      const totalInput = this._totalInput();
      if (!totalInput) return;
      const total = parseInt(totalInput.value, 10) || 0;

      const html = this.$refs.template.innerHTML.replaceAll(
        "__prefix__",
        String(total)
      );
      this.$refs.list.insertAdjacentHTML("beforeend", html);
      totalInput.value = String(total + 1);
      this._renumber();

      this.$nextTick(() => {
        const newItem = this.$refs.list.lastElementChild;
        if (!newItem) return;
        newItem.scrollIntoView({ behavior: "smooth", block: "center" });
        const firstInput = newItem.querySelector(
          'textarea:not([type=hidden]), input[type=text]'
        );
        if (firstInput) firstInput.focus();
      });
    },

    __remove(card) {
      if (!card) return;
      card.querySelectorAll("input, textarea").forEach((el) => {
        if (el.type === "hidden") return;
        if (el.type === "file") {
          el.value = "";
          return;
        }
        if (el.type === "checkbox" || el.type === "radio") {
          el.checked = false;
          return;
        }
        el.value = "";
      });
      card.classList.add("bo-collapse-card-hidden");
    },

    _renumber() {
      const items = this.$refs.list.querySelectorAll(
        ":scope > li:not(.bo-collapse-card-hidden)"
      );
      let idx = 0;
      items.forEach((li) => {
        const orderInput = li.querySelector('input[name$="-order"]');
        if (orderInput) orderInput.value = String(idx);
        idx += 1;
      });
    },

    _totalInput() {
      const prefix = this.$root.dataset.prefix || "";
      return this.$root.querySelector(
        `input[name="${prefix}-TOTAL_FORMS"]`
      );
    },
  }));

  Alpine.data(
    "boInlineCollapseCard",
    ({
      initialOpen,
      initialPhoto,
      placeholderLabel,
      summaryPrimary,
      summarySecondary,
    } = {}) => ({
      open: !!initialOpen,
      photoUrl: initialPhoto || "",
      placeholderLabel: placeholderLabel || "Новая запись",
      displayName: "",
      displaySecondary: "",
      markedForDelete: false,

      _primary: summaryPrimary || "",
      _secondary: summarySecondary || "",

      init() {
        this._refreshSummary();

        const watchSelectors = [];
        if (this._primary) watchSelectors.push(`[name*="-${this._primary}_"]`);
        if (this._secondary) watchSelectors.push(`[name*="-${this._secondary}_"]`);
        if (watchSelectors.length) {
          this.$el.querySelectorAll(watchSelectors.join(",")).forEach((el) => {
            el.addEventListener("input", () => this._refreshSummary());
            el.addEventListener("change", () => this._refreshSummary());
          });
        }

        const del = this.$el.querySelector('input[name$="-DELETE"]');
        if (del) {
          this.markedForDelete = del.checked;
          del.addEventListener("change", () => {
            this.markedForDelete = del.checked;
          });
        }
      },

      _firstNonEmpty(base) {
        if (!base) return "";
        for (const lang of ["ru", "kk", "en"]) {
          const el = this.$el.querySelector(`[name$="-${base}_${lang}"]`);
          if (el && (el.value || "").trim()) return el.value.trim();
        }
        return "";
      },

      _refreshSummary() {
        this.displayName = this._firstNonEmpty(this._primary);
        this.displaySecondary = this._firstNonEmpty(this._secondary);
      },

      onPhotoChange(ev) {
        const file = ev.target.files && ev.target.files[0];
        if (!file) return;
        if (this._objUrl) URL.revokeObjectURL(this._objUrl);
        this._objUrl = URL.createObjectURL(file);
        this.photoUrl = this._objUrl;
        this.open = true;
      },
    })
  );
}
