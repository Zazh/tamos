/* Alpine компонент для backoffice раздела «Команда».
 *
 * boTeamSort — Sortable.js на списке членов команды одной группы (featured /
 *   other). После drop — AJAX POST с {group, order:[pk1, pk2, ...]} на
 *   reorder URL. Order пишется как i*10 на сервере. is_featured НЕ меняется
 *   этим эндпоинтом — для смены группы менеджер открывает edit.
 *
 * DOM:
 *   <ul x-data="boTeamSort"
 *       data-group="featured"
 *       data-reorder-url="/backoffice/content/team/region/1/reorder/">
 *     <li data-pk="42">…</li>
 *     <li data-pk="43">…</li>
 *   </ul>
 */
import Sortable from "sortablejs";

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[2]) : "";
}

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify(body),
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

function boTeamSort() {
  return {
    init() {
      const group = this.$root.dataset.group;
      const url = this.$root.dataset.reorderUrl;
      if (!group || !url) return;

      Sortable.create(this.$root, {
        animation: 150,
        handle: ".bo-drag-handle",
        ghostClass: "bo-team-row-ghost",
        onEnd: async () => {
          const order = Array.from(this.$root.children)
            .map((el) => parseInt(el.dataset.pk, 10))
            .filter(Boolean);
          try {
            await postJSON(url, { group, order });
          } catch (e) {
            console.error("Team reorder failed:", e);
          }
        },
      });
    },
  };
}

export function registerBackofficeTeam(Alpine) {
  Alpine.data("boTeamSort", boTeamSort);
}
