/* Расширение Trix toolbar в backoffice (blog / events / ...):
 *   - h2 / h3 как новые block-attributes
 *   - кнопки H2 / H3 в toolbar (вместо стандартной H1 = заголовок страницы)
 *   - кнопка YouTube → вставляет [[youtube id=...]] (фильтр render_youtube
 *     заменит на <iframe> при рендере публичной страницы)
 *
 * Подключение в head edit-страницы ДО Trix CDN (см. edit.html):
 *   <script src="{% static 'js/backoffice-trix-setup.js' %}"></script>
 *   <script src=".../trix.umd.min.js" defer></script>
 *
 * Порядок важен: наш скрипт синхронный — успевает добавить listener'ы на
 * document до того, как Trix зарегистрирует custom-element и эмитит
 * trix-before-initialize при connectedCallback существующих <trix-editor>.
 *
 * Файл живёт в backoffice/static/ (а НЕ в общем tamosapp/app/static/),
 * потому что Vite-билд (`emptyOutDir: true`) стирает корневой static перед
 * сборкой. Django collectstatic тянет static из app-директорий поверх.
 */
(function () {
  'use strict';

  document.addEventListener('trix-before-initialize', extendConfig, { capture: true });
  document.addEventListener('trix-initialize', initToolbar, { capture: true });

  function extendConfig() {
    if (!window.Trix) return;
    var ba = window.Trix.config.blockAttributes;

    // Обычный абзац как <p>, а не <div> (дефолт Trix). Семантика +
    // совместимость с .content-redactor :where(p, li) стилями на сайте.
    if (ba.default && ba.default.tagName === 'div') {
      ba.default.tagName = 'p';
    }

    if (!ba.heading2) {
      ba.heading2 = { tagName: 'h2', terminal: true, breakOnReturn: true, group: false };
    }
    if (!ba.heading3) {
      ba.heading3 = { tagName: 'h3', terminal: true, breakOnReturn: true, group: false };
    }
  }

  function initToolbar(event) {
    var editor = event.target;
    var toolbar = editor.toolbarElement;
    if (!toolbar || toolbar.dataset.boExtended === '1') return;
    toolbar.dataset.boExtended = '1';

    var buttonRow = toolbar.querySelector('.trix-button-row');
    if (!buttonRow) return;

    var blockTools = toolbar.querySelector('[data-trix-button-group="block-tools"]');
    if (blockTools) {
      // Убираем стандартную H1 (h1 = заголовок поста, рендерится снаружи)
      var h1 = blockTools.querySelector('[data-trix-attribute="heading1"]');
      if (h1) h1.remove();

      var h3 = buildBlockBtn('heading3', 'H3', 'Подзаголовок (H3)');
      var h2 = buildBlockBtn('heading2', 'H2', 'Подзаголовок (H2)');
      blockTools.insertBefore(h3, blockTools.firstChild);
      blockTools.insertBefore(h2, h3);
    }

    // Группа со вставкой YouTube — перед file-tools (или в конце)
    var fileTools = toolbar.querySelector('[data-trix-button-group="file-tools"]');
    var ytGroup = document.createElement('span');
    ytGroup.className = 'trix-button-group bo-trix-extras';
    ytGroup.setAttribute('data-trix-button-group', 'extras');

    var ytBtn = document.createElement('button');
    ytBtn.type = 'button';
    ytBtn.className = 'trix-button bo-trix-btn-youtube';
    ytBtn.tabIndex = -1;
    ytBtn.title = 'Вставить видео с YouTube';
    ytBtn.setAttribute('aria-label', 'Вставить видео с YouTube');
    ytBtn.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
      'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<rect x="2" y="5" width="20" height="14" rx="3"/>' +
      '<path d="M10 9.5v5l4-2.5z" fill="currentColor" stroke="none"/>' +
      '</svg>';

    ytBtn.addEventListener('click', function () {
      onInsertYoutube(editor);
    });

    ytGroup.appendChild(ytBtn);

    if (fileTools && fileTools.parentNode) {
      fileTools.parentNode.insertBefore(ytGroup, fileTools);
    } else {
      buttonRow.appendChild(ytGroup);
    }
  }

  function buildBlockBtn(attr, label, title) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.tabIndex = -1;
    btn.setAttribute('data-trix-attribute', attr);
    // НЕТ класса trix-button--icon: он скрывает текст через text-indent:-9999px.
    // Кнопки H2/H3 текстовые, не иконочные.
    btn.className = 'trix-button bo-trix-btn-text bo-trix-btn-' + attr;
    btn.title = title;
    btn.setAttribute('aria-label', title);
    btn.textContent = label;
    return btn;
  }

  function onInsertYoutube(editor) {
    var input = window.prompt(
      'Вставь ссылку YouTube или ID видео:\n' +
      '— https://youtu.be/dQw4w9WgXcQ\n' +
      '— https://www.youtube.com/watch?v=dQw4w9WgXcQ\n' +
      '— dQw4w9WgXcQ'
    );
    if (input == null) return;
    var id = extractYoutubeId(input);
    if (!id) {
      window.alert('Не удалось распознать ID видео. Скопируй URL целиком из адресной строки YouTube.');
      return;
    }
    if (!editor || !editor.editor) return;
    // Вставляем шорткод отдельным абзацем — на рендере он развернётся в iframe.
    editor.editor.insertString('[[youtube id=' + id + ']]');
    editor.editor.insertLineBreak();
  }

  function extractYoutubeId(raw) {
    var s = String(raw || '').trim();
    if (!s) return null;
    if (/^[A-Za-z0-9_-]{11}$/.test(s)) return s;
    var patterns = [
      /[?&]v=([A-Za-z0-9_-]{11})/,
      /youtu\.be\/([A-Za-z0-9_-]{11})/,
      /youtube\.com\/embed\/([A-Za-z0-9_-]{11})/,
      /youtube\.com\/shorts\/([A-Za-z0-9_-]{11})/,
      /youtube\.com\/live\/([A-Za-z0-9_-]{11})/
    ];
    for (var i = 0; i < patterns.length; i++) {
      var m = s.match(patterns[i]);
      if (m) return m[1];
    }
    return null;
  }
})();
