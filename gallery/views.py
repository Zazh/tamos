from django.views.generic import ListView

from .models import GalleryCategory, GalleryImage


IMAGES_PER_PAGE = 24


class GalleryListView(ListView):
    """Фотогалерея филиала. Фильтр по `?category=<slug>`."""

    template_name = 'gallery/list.html'
    context_object_name = 'images'
    paginate_by = IMAGES_PER_PAGE

    def get_queryset(self):
        region = self.request.region
        qs = (
            GalleryImage.objects
            .filter(region=region, is_published=True)
            .exclude(image='')
            .select_related('category')
            .order_by('order', '-created_at', '-pk')
        )
        category_slug = self.request.GET.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = list(
            GalleryCategory.objects.filter(is_published=True).order_by('order', 'name'),
        )
        ctx['current_category_slug'] = self.request.GET.get('category') or ''
        return ctx
