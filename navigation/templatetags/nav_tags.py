from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_url(context, item):
    """
    URL для пункта навигации NavItem с учётом текущего региона.
    Пустой `url_name` или NoReverseMatch → `#` (пункт-заглушка, страница
    ещё не реализована — ссылка видна, но никуда не ведёт).
    """
    if not item.url_name:
        return '#'
    request = context.get('request')
    region = getattr(request, 'region', None) if request else None
    kwargs = {'region_slug': region.slug} if region is not None else {}
    try:
        return reverse(item.url_name, kwargs=kwargs)
    except NoReverseMatch:
        return '#'
