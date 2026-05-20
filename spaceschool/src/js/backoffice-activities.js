/* Alpine компоненты для backoffice раздела «Активности».
 *
 * boActivitySort — Sortable.js на каталоге активностей региона. После drop —
 *   AJAX POST с новым порядком (по секции).
 * boSlotFormset — простой add/remove для inline-formset слотов на странице
 *   edit Group. Аналог boInlineCollapse, но без open/close и Sortable
 *   (slot'ы короткие, drag не нужен — порядок задаётся данными по `day`).
 */
import Sortable from "sortablejs";

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[2]) : "";
}

async function fetchJSON(url, opts = {}) {
  const headers = Object.assign(
    { "X-CSRFToken": getCookie("csrftoken") },
    opts.headers || {},
  );
  if (opts.body && !(opts.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(url, {
    method: opts.method || "GET",
    headers,
    body: opts.body
      ? opts.body instanceof FormData
        ? opts.body
        : JSON.stringify(opts.body)
      : undefined,
    credentials: "same-origin",
  });
  const raw = await res.text();
  let data;
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch (_) {
    data = null;
  }
  if (!res.ok) {
    const detail = (data && data.error) || raw || "";
    throw new Error(detail.slice(0, 300) || `HTTP ${res.status}`);
  }
  return data || {};
}

/* boActivitySort — DnD на каталоге кружков. Один компонент на секцию. */
function boActivitySort() {
  return {
    init() {
      const sectionPk = parseInt(this.$root.dataset.sectionPk, 10);
      const url = this.$root.dataset.reorderUrl;
      if (!sectionPk || !url) return;

      Sortable.create(this.$root, {
        animation: 150,
        handle: ".bo-drag-handle",
        ghostClass: "bo-activity-accordion-ghost",
        onEnd: async () => {
          const order = Array.from(this.$root.children)
            .map((el) => parseInt(el.dataset.pk, 10))
            .filter(Boolean);
          try {
            await fetchJSON(url, {
              method: "POST",
              body: { section_pk: sectionPk, order },
            });
          } catch (e) {
            console.error("Reorder failed:", e);
          }
        },
      });
    },
  };
}

/* boSlotFormset — простой add/remove для ScheduleSlot inline-formset на group_edit.
 *
 * DOM:
 *   <div x-data="boSlotFormset" data-prefix="slots">
 *     {{ formset.management_form }}
 *     <ul x-ref="list"><li>...</li></ul>
 *     <template x-ref="template"><li>...empty_form...</li></template>
 *     <button @click="add()">+ Добавить</button>
 *   </div>
 */
function boSlotFormset() {
  return {
    add() {
      const totalInput = this._totalInput();
      if (!totalInput) return;
      const total = parseInt(totalInput.value, 10) || 0;
      const html = this.$refs.template.innerHTML.replaceAll(
        "__prefix__",
        String(total),
      );
      this.$refs.list.insertAdjacentHTML("beforeend", html);
      totalInput.value = String(total + 1);
    },

    __remove(row) {
      if (!row) return;
      // Очищаем поля и скрываем — TOTAL_FORMS не уменьшаем (Django пропустит пустую extra).
      row.querySelectorAll("input, select, textarea").forEach((el) => {
        if (el.type === "hidden") return;
        if (el.type === "checkbox" || el.type === "radio") {
          el.checked = false;
          return;
        }
        el.value = "";
      });
      row.style.display = "none";
    },

    _totalInput() {
      const prefix = this.$root.dataset.prefix || "";
      return this.$root.querySelector(`input[name="${prefix}-TOTAL_FORMS"]`);
    },
  };
}

export function registerBackofficeActivities(Alpine) {
  Alpine.data("boActivitySort", boActivitySort);
  Alpine.data("boSlotFormset", boSlotFormset);
}
