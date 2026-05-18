"""Inline-SVG icons для backoffice sidebar.

Икона — путь(и) внутри стандартного 24×24 viewBox, stroke-currentColor.
Чтобы добавить новую: вставить запись в ICONS — `name: '<path .../>'`.
Размер задаётся снаружи через class — см. `.bo-icon` в backoffice-shell.css.

Lucide-style: stroke-width 1.5, stroke-linecap/linejoin round.
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


ICONS = {
    # 2×2 squares — dashboard
    'dashboard': (
        '<rect x="3" y="3" width="7" height="7" rx="1"/>'
        '<rect x="14" y="3" width="7" height="7" rx="1"/>'
        '<rect x="3" y="14" width="7" height="7" rx="1"/>'
        '<rect x="14" y="14" width="7" height="7" rx="1"/>'
    ),
    # inbox
    'inbox': (
        '<path d="M22 12h-6l-2 3h-4l-2-3H2"/>'
        '<path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>'
    ),
    'home': (
        '<path d="M3 12l9-9 9 9"/>'
        '<path d="M5 10v10a1 1 0 0 0 1 1h3v-6h6v6h3a1 1 0 0 0 1-1V10"/>'
    ),
    'phone': (
        '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.37 1.9.72 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.35 1.85.59 2.81.72a2 2 0 0 1 1.72 2.02z"/>'
    ),
    # graduation cap
    'cap': (
        '<path d="M22 10v6"/>'
        '<path d="M2 10l10-5 10 5-10 5z"/>'
        '<path d="M6 12v5a6 6 0 0 0 12 0v-5"/>'
    ),
    'target': (
        '<circle cx="12" cy="12" r="10"/>'
        '<circle cx="12" cy="12" r="6"/>'
        '<circle cx="12" cy="12" r="2"/>'
    ),
    # activity pulse
    'pulse': (
        '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>'
    ),
    'newspaper': (
        '<path d="M4 22h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/>'
        '<path d="M18 14h-8M15 18h-5M10 6h8v4h-8z"/>'
    ),
    'sparkles': (
        '<path d="M12 3l1.9 5.6L19.5 10l-5.6 1.4L12 17l-1.9-5.6L4.5 10l5.6-1.4z"/>'
        '<path d="M19 14l.7 2 2 .7-2 .7L19 19.5l-.7-2.1-2-.7 2-.7z"/>'
        '<path d="M5 4l.5 1.5L7 6l-1.5.5L5 8l-.5-1.5L3 6l1.5-.5z"/>'
    ),
    'image': (
        '<rect x="3" y="3" width="18" height="18" rx="2"/>'
        '<circle cx="9" cy="9" r="2"/>'
        '<path d="M21 15l-5-5L5 21"/>'
    ),
    'file': (
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>'
    ),
    'menu': (
        '<line x1="3" y1="6" x2="21" y2="6"/>'
        '<line x1="3" y1="12" x2="21" y2="12"/>'
        '<line x1="3" y1="18" x2="21" y2="18"/>'
    ),
    'pin': (
        '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/>'
        '<circle cx="12" cy="10" r="3"/>'
    ),
    'users': (
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
        '<circle cx="9" cy="7" r="4"/>'
        '<path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>'
    ),
    # external-link (для admin-fallback значков)
    'external': (
        '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
        '<polyline points="15 3 21 3 21 9"/>'
        '<line x1="10" y1="14" x2="21" y2="3"/>'
    ),
    # burger
    'burger': (
        '<line x1="3" y1="6" x2="21" y2="6"/>'
        '<line x1="3" y1="12" x2="21" y2="12"/>'
        '<line x1="3" y1="18" x2="21" y2="18"/>'
    ),
    'close': (
        '<line x1="6" y1="6" x2="18" y2="18"/>'
        '<line x1="18" y1="6" x2="6" y2="18"/>'
    ),
}


SVG_TEMPLATE = (
    '<svg class="bo-icon {extra}" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">{body}</svg>'
)


@register.simple_tag
def bo_icon(name, extra=''):
    body = ICONS.get(name, '')
    if not body:
        return mark_safe(f'<!-- bo_icon: unknown name {name!r} -->')
    return mark_safe(SVG_TEMPLATE.format(extra=extra, body=body))


@register.filter
def getfield(form, name):
    """Получить BoundField из формы по имени, рассчитанному в шаблоне.

    Используется для рендера переводимых полей `<base>_<lang>` через include
    с переменной `base`. Без этого filter в шаблоне нельзя обратиться к
    `form.<динамическое имя>`.
    """
    try:
        return form[name]
    except KeyError:
        return None


@register.filter
def getbyindex(seq, i):
    """Индексный доступ к sequence из шаблона. Нужен потому что нельзя
    `seq.0`/`seq.1` если ключи — числа. Используется в backoffice/content/program/edit.html
    для распаковки конфигурации `formsets` (список из 7 кортежей)."""
    try:
        return seq[int(i)]
    except (IndexError, TypeError, ValueError):
        return None


@register.filter(name='get_item')
def get_item(d, key):
    """`{{ mapping|get_item:dynamic_key }}` — доступ к dict по динамическому ключу.

    Стандартный `{{ d.42 }}` работает только для строковых ключей,
    `{{ d.activity.pk }}` Django парсит как путь атрибутов, не как ключ.
    """
    if d is None:
        return None
    try:
        return d.get(key) if hasattr(d, 'get') else d[key]
    except (KeyError, TypeError):
        return None


@register.filter(name='getattr')
def getattr_filter(obj, name):
    """`{{ obj|getattr:'field_name' }}` — атрибут по строке. Используется в
    `_photo_field.html` чтобы получить ImageField по имени переменной."""
    return getattr(obj, name, None)


@register.simple_tag
def field_help(key):
    """Раскрывающаяся инструкция для CMS-поля. Контент из `pages.field_help`.

    Запись содержит `html` и флаг `ai_processable`:
    - True (текстовые поля) — summary показывает «📖 Инструкция · AI-промпт»
    - False (image/video) — summary показывает «📖 Инструкция · только вручную»
      и в начало body добавляется предупреждение
    """
    from pages.field_help import FIELD_HELP
    entry = FIELD_HELP.get(key)
    if not entry:
        return ''
    body = entry.get('html', '').strip()
    if not body:
        return ''
    ai = entry.get('ai_processable', True)
    summary_label = (
        '📖 Инструкция · AI-промпт · референс'
        if ai
        else '📖 Инструкция · 🚫 без AI · референс'
    )
    if not ai:
        body = (
            '<div class="bo-help-noai">'
            '🚫 <strong>Не обрабатывается AI-помощником.</strong> Это поле '
            'требует бинарного файла (картинка/видео) — LLM такое не генерирует. '
            'Используй Midjourney/Photoshop для картинок, HandBrake/CapCut для видео.'
            '</div>'
            + body
        )
    return mark_safe(
        f'<details class="bo-help-disclosure" data-ai-processable="{str(ai).lower()}">'
        '<summary class="bo-help-disclosure-toggle">'
        f'<span>{summary_label}</span>'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M6 9l6 6 6-6"/></svg>'
        '</summary>'
        f'<div class="bo-help-disclosure-body">{body}</div>'
        '</details>'
    )
