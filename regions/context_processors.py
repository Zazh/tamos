from django.utils.translation import get_language

from .models import Region


def regions_and_language(request):
    """Кладёт в шаблоны список регионов и текущий язык, чтобы header не лез в БД сам."""
    return {
        'all_regions': Region.objects.all(),
        'current_region': getattr(request, 'region', None),
        'current_language': get_language(),
    }
