import re

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()

GALLERY_SHORTCODE = re.compile(r'\[\[gallery\s+slug=([\w-]+)\]\]')


@register.filter(name='render_galleries')
def render_galleries(content, post):
    """Заменяет шорткоды `[[gallery slug=NAME]]` на отрендеренные галереи.

    Неизвестные slug просто вырезаются (без сообщения об ошибке на странице).
    Если шорткодов нет — возвращаем контент as-is через mark_safe (контент
    в BlogPost.content всё равно хранится как доверенный HTML и рендерится
    через |safe в шаблоне).
    """

    raw = content or ''
    if '[[gallery' not in raw:
        return mark_safe(raw)

    galleries = {
        gallery.slug: gallery
        for gallery in post.galleries.prefetch_related('images').all()
    }

    def replace(match):
        slug = match.group(1)
        # 'main' рендерится отдельно ПОСЛЕ content в detail.html — если в текст
        # случайно вставили [[gallery slug=main]], схлопываем чтобы не дублировать.
        if slug == 'main':
            return ''
        gallery = galleries.get(slug)
        if gallery is None:
            return ''
        return render_to_string('blog/_gallery.html', {'gallery': gallery})

    return mark_safe(GALLERY_SHORTCODE.sub(replace, raw))
