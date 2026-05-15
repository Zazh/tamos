from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_url(context, item):
    """
    URL для пункта навигации NavItem с учётом текущего региона.

    Приоритет:
      1) `item.flat_page` → reverse('pages:flat', slug=...) — статичные
         страницы (О нас, форма, privacy и т.п.).
      2) `item.url_name` → reverse(url_name) — обычные view-страницы.
      3) иначе → `#` (заглушка).
    """
    request = context.get('request')
    region = getattr(request, 'region', None) if request else None
    region_kwargs = {'region_slug': region.slug} if region is not None else {}

    if item.flat_page_id:
        try:
            return reverse(
                'pages:flat',
                kwargs={**region_kwargs, 'slug': item.flat_page.slug},
            )
        except NoReverseMatch:
            return '#'

    if not item.url_name:
        return '#'

    try:
        return reverse(item.url_name, kwargs=region_kwargs)
    except NoReverseMatch:
        return '#'
