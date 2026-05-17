import Sortable from "sortablejs";

/**
 * boInlineSort — drag-and-drop сортировка для Django inline-formset'ов в backoffice.
 *
 * Применяется к <ul class="bo-formset"> на edit-странице Программы (7 inline-formset'ов).
 * Поле `order` рендерится как hidden <input> внутри каждого <li>. После drag-end JS
 * обходит <li> в новом порядке и записывает их индексы в hidden inputs — при submit
 * сервер сохраняет обновлённый порядок.
 *
 * Каждый <li> должен иметь drag-handle с классом `bo-drag-handle` (только эта область
 * захватывает движение мышью — иначе случайные drag'и при работе с textarea).
 */
export function registerBackofficeInlineSort(Alpine) {
  Alpine.data("boInlineSort", () => ({
    init() {
      Sortable.create(this.$el, {
        animation: 150,
        handle: ".bo-drag-handle",
        ghostClass: "bo-formset-item-ghost",
        onEnd: () => this._renumber(),
      });
    },

    _renumber() {
      const items = this.$el.querySelectorAll(":scope > li");
      items.forEach((li, idx) => {
        const input = li.querySelector(
          'input[name$="-order"]'
        );
        if (input) input.value = String(idx);
      });
    },
  }));
}
