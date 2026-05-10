from django.http import HttpResponseRedirect, HttpResponseServerError
from django.urls import reverse

from regions.models import Region


def root_redirect(request):
    """
    `/` → `/<region>/`. Берём cookie 'region' если стоит,
    иначе Region.is_default=True, иначе первый существующий регион.
    """
    cookie = request.COOKIES.get('region')
    region = Region.objects.filter(slug=cookie).first() if cookie else None
    if region is None:
        region = Region.get_default() or Region.objects.first()
    if region is None:
        return HttpResponseServerError('No regions configured.')
    return HttpResponseRedirect(reverse('pages:home', kwargs={'region_slug': region.slug}))
