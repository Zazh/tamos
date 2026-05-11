from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import override

from regions.models import Region

# Pages exposed in sitemap.xml. Add new public pages here.
SEO_PAGES = ['pages:home', 'pages:contacts', 'pages:gallery']


def root_redirect(request):
    """
    `/` → `/<region>/`. Берём cookie 'region' если стоит,
    иначе Region.is_default=True, иначе первый существующий регион.
    """
    cookie = request.COOKIES.get('region')
    region = Region.objects.filter(slug=cookie, is_active=True).first() if cookie else None
    if region is None:
        region = Region.get_default() or Region.objects.filter(is_active=True).first()
    if region is None:
        return HttpResponseServerError('No active regions configured.')
    return HttpResponseRedirect(reverse('pages:home', kwargs={'region_slug': region.slug}))


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse('sitemap'))
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /i18n/setlang/',
        '',
        f'Sitemap: {sitemap_url}',
        '',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')


def llms_txt(request):
    default_region = Region.get_default() or Region.objects.filter(is_active=True).first()
    slug = default_region.slug if default_region else 'astana'
    ctx = {
        'site_url': request.build_absolute_uri('/').rstrip('/'),
        'home_url': request.build_absolute_uri(reverse('pages:home', kwargs={'region_slug': slug})),
        'contacts_url': request.build_absolute_uri(reverse('pages:contacts', kwargs={'region_slug': slug})),
        'gallery_url': request.build_absolute_uri(reverse('pages:gallery', kwargs={'region_slug': slug})),
    }
    return render(request, 'llms.txt', ctx, content_type='text/plain; charset=utf-8')


def sitemap_xml(request):
    from django.conf import settings as dj_settings

    langs = [code for code, _ in dj_settings.LANGUAGES]
    regions = list(Region.objects.filter(is_active=True))

    urls = []
    for region in regions:
        for view_name in SEO_PAGES:
            for lang in langs:
                with override(lang):
                    path = reverse(view_name, kwargs={'region_slug': region.slug})
                urls.append(request.build_absolute_uri(path))

    return render(request, 'sitemap.xml', {'urls': urls}, content_type='application/xml; charset=utf-8')
