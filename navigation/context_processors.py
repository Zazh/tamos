from django.db.models import Prefetch

from .models import NavItem, NavSection


def navigation(request):
    """
    Кладёт в шаблоны две выборки:
    - `nav_top_items`     — пункты для верхней навигации (is_top_nav=True).
    - `nav_mega_sections` — все секции мегаменю с прифетченными опубликованными
                            пунктами (через `section.items_published`).

    Запросы делаются ленивo: если шаблон не итерирует — БД не трогаем.
    Пустая БД (свежий накат до миграции seed) безопасна — выборки будут пустыми.
    """
    published_items = NavItem.objects.filter(is_published=True).order_by('order', 'pk')
    return {
        'nav_top_items': published_items.filter(is_top_nav=True),
        'nav_mega_sections': (
            NavSection.objects
            .order_by('order', 'slug')
            .prefetch_related(Prefetch('items', queryset=published_items, to_attr='items_published'))
        ),
    }
