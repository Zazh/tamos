"""Общие фильтры для HTML-контента из CMS (blog / events / flatpages / ...).

`render_youtube` делает две вещи:
  1. Нормализует legacy-Trix-разметку: голый `<div>...</div>` (дефолтный
     блок Trix до того, как мы переключили default tagName на 'p') →
     `<p>...</p>`. Это даёт `.content-redactor :where(p)` стили (синие
     ссылки, line-height) на старых записях.
  2. Разворачивает `[[youtube id=XXX]]` (в т. ч. одиноко обёрнутый в `<p>`
     Trix'ом) в `<figure class="content-video">` с responsive iframe-embed.

Шорткод вставляется кнопкой в backoffice-Trix-редакторе.
"""

import re

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()

# `<div>...</div>` БЕЗ атрибутов на открывающем теге — это legacy-абзац от
# Trix. Любой div с class/id/style оставляем — он наш (.content-video__frame,
# и т.п.) или пришёл из встроенного HTML. Trix не вкладывает div в div,
# поэтому non-greedy match безопасен.
_BARE_DIV_PAIR = re.compile(r'<div>([\s\S]*?)</div>', re.IGNORECASE)

# id YouTube-видео — ровно 11 символов из [A-Za-z0-9_-].
_YT_INLINE = re.compile(r'\[\[youtube\s+id=([A-Za-z0-9_-]{11})\]\]')
_YT_WRAPPED_P = re.compile(
    r'<p>\s*\[\[youtube\s+id=([A-Za-z0-9_-]{11})\]\]\s*</p>',
    re.IGNORECASE,
)


@register.filter(name='render_youtube')
def render_youtube(content):
    """Применяет нормализацию `<div>→<p>` и разворачивает YouTube-шорткоды.

    Принимает уже-mark_safe строку (если фильтр идёт после `|render_galleries`)
    или обычный HTML — в обоих случаях возвращает mark_safe HTML.
    """

    raw = content or ''
    if not raw:
        return mark_safe(raw)

    # 1. Legacy <div>...</div> от Trix → <p>...</p>. Заменяем ДО рендера
    # YouTube, чтобы обёртка вокруг [[youtube]] стала <p>...</p> и сработал
    # _YT_WRAPPED_P (он матчит именно <p>).
    raw = _BARE_DIV_PAIR.sub(r'<p>\1</p>', raw)

    if '[[youtube' not in raw:
        return mark_safe(raw)

    def _embed(video_id):
        return render_to_string('partials/_youtube_embed.html', {'video_id': video_id})

    # Шорткод, обёрнутый в одиночный <p>...</p>, — заменяем целиком, чтобы
    # не получить невалидный <p><figure>…</figure></p>.
    raw = _YT_WRAPPED_P.sub(lambda m: _embed(m.group(1)), raw)
    # Любые оставшиеся вхождения шорткода (внутри текста, без обёртки).
    raw = _YT_INLINE.sub(lambda m: _embed(m.group(1)), raw)
    return mark_safe(raw)
