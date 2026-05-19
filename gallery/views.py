from django.views.generic import ListView

from .models import GalleryCategory, GalleryImage


IMAGES_PER_PAGE = 24


def _strict_zip_arrange(images):
    """Чередуем wide/normal для красивой мозаики на странице галереи.

    Алгоритм: разбиваем на wide и normal списки, потом поочерёдно берём по
    одному из каждого ([N, W, N, W, ...]), если хвост остаётся — он идёт в
    конец. Внутри каждого списка порядок сохраняется (он уже отсортирован
    `-created_at` на уровне queryset).

    Этот же паттерн используется в HomePage gallery (см.
    `backoffice/views.py::_strict_zip_arrange` — там для боковой mosaic). Цель
    — чтобы wide-карточки не сваливались кучкой в одно место, а распределялись
    по странице.
    """
    wides = [i for i in images if i.is_wide]
    normals = [i for i in images if not i.is_wide]
    out = []
    while wides or normals:
        # Начинаем с normal (1 колонка), потом wide (2 колонки) — чередование
        # `1+2+1+2+…` хорошо заполняет 3-колоночную сетку без больших дыр.
        if normals:
            out.append(normals.pop(0))
        if wides:
            out.append(wides.pop(0))
    return out


class GalleryListView(ListView):
    """Фотогалерея региона. Плоская лента всех фото из опубликованных альбомов
    региона, отсортированная `-created_at`. Фильтр по `?category=<slug>` —
    через FK на Album.
    """

    template_name = 'gallery/list.html'
    context_object_name = 'images'
    paginate_by = IMAGES_PER_PAGE

    def get_queryset(self):
        region = self.request.region
        qs = (
            GalleryImage.objects
            .filter(
                album__region=region,
                album__is_published=True,
                is_published=True,
            )
            .exclude(image='')
            .select_related('album', 'album__category')
            .order_by('-created_at', '-pk')
        )
        category_slug = self.request.GET.get('category')
        if category_slug:
            qs = qs.filter(album__category__slug=category_slug)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = list(
            GalleryCategory.objects.filter(is_published=True).order_by('order', 'name'),
        )
        ctx['current_category_slug'] = self.request.GET.get('category') or ''
        # Перетасуем картинки на странице так, чтобы wide и normal чередовались.
        # Pagination уже применился (object_list = текущая страница), strict-zip
        # работает только внутри страницы — это нормально, mosaic-сетка в любом
        # случае рендерит постранично.
        ctx['images'] = _strict_zip_arrange(list(ctx['images']))
        ctx['object_list'] = ctx['images']
        return ctx
