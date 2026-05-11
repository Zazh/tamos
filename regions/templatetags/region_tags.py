from django import template
from django.urls import NoReverseMatch, reverse
from django.utils.translation import override

register = template.Library()


@register.simple_tag(takes_context=True)
def regions_inline_list(context, separator=", "):
    """
    Перечисление имён всех регионов через запятую — для meta-описаний и
    подобных мест, где «Astana, Aktau» должно автоматически обновляться при
    добавлении нового региона. `name` берётся через modeltranslation в текущем
    языке. Источник — `all_regions` из context_processor.
    """
    regions = context.get('all_regions') or []
    return separator.join(str(r.name) for r in regions if r.name)


@register.simple_tag(takes_context=True)
def region_url(context, name, *args, **kwargs):
    """
    Реверс URL внутри текущего региона: автоматически подставляет region_slug
    из request.region. Если регион не задан в контексте — нужно передать руками.

        {% region_url 'pages:home' %}            → /ru/astana/
        {% region_url 'pages:contacts' %}        → /ru/astana/contacts/
    """
    request = context.get('request')
    region = getattr(request, 'region', None) if request else None
    if region is not None and 'region_slug' not in kwargs:
        kwargs['region_slug'] = region.slug
    return reverse(name, args=args, kwargs=kwargs)


@register.simple_tag(takes_context=True)
def switch_region_url(context, region):
    """
    URL для переключения на другой регион, сохраняя текущую страницу и язык.

        {% switch_region_url r %}                → /<lang>/<r.slug>/<тот же view>/
    """
    request = context.get('request')
    if request is None:
        return reverse('pages:home', kwargs={'region_slug': region.slug})
    match = request.resolver_match
    if not match or not match.url_name:
        return reverse('pages:home', kwargs={'region_slug': region.slug})
    kwargs = {**(match.kwargs or {}), 'region_slug': region.slug}
    name = f'{match.namespace}:{match.url_name}' if match.namespace else match.url_name
    try:
        return reverse(name, kwargs=kwargs)
    except NoReverseMatch:
        return reverse('pages:home', kwargs={'region_slug': region.slug})


@register.simple_tag(takes_context=True)
def switch_language_url(context, language_code):
    """
    URL текущей страницы под другим языком. Использует translation.override,
    чтобы reverse подставил правильный языковой префикс
    (prefix_default_language=True — префикс есть у всех языков, включая ru).
    """
    request = context.get('request')
    if request is None:
        return '/'
    match = request.resolver_match
    if not match or not match.url_name:
        return '/'
    kwargs = match.kwargs or {}
    name = f'{match.namespace}:{match.url_name}' if match.namespace else match.url_name
    with override(language_code):
        try:
            return reverse(name, kwargs=kwargs)
        except NoReverseMatch:
            return '/'
