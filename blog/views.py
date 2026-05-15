from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .models import BlogCategory, BlogPost, BlogTag


POSTS_PER_PAGE = 9
RELATED_POSTS_COUNT = 3


class BlogListView(ListView):
    """Лента статей блога. Фильтр по `?category=<slug>` или `?tag=<slug>`."""

    template_name = 'blog/list.html'
    context_object_name = 'posts'
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        region = self.request.region
        qs = (
            BlogPost.objects
            .filter(region=region, is_published=True)
            .select_related('category')
            .order_by('-published_at', '-pk')
        )

        category_slug = self.request.GET.get('category')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        region = self.request.region
        ctx['categories'] = list(
            BlogCategory.objects.filter(region=region).order_by('order', 'name'),
        )
        ctx['current_category_slug'] = self.request.GET.get('category') or ''
        ctx['current_tag_slug'] = self.request.GET.get('tag') or ''
        if ctx['current_tag_slug']:
            ctx['current_tag'] = (
                BlogTag.objects
                .filter(region=region, slug=ctx['current_tag_slug'])
                .first()
            )
        return ctx


class BlogDetailView(DetailView):
    template_name = 'blog/detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        region = self.request.region
        return get_object_or_404(
            BlogPost.objects
            .filter(region=region, is_published=True)
            .select_related('category')
            .prefetch_related('tags'),
            slug=self.kwargs['slug'],
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        post = ctx['post']
        related = (
            BlogPost.objects
            .filter(
                region=post.region,
                is_published=True,
                category=post.category,
            )
            .exclude(pk=post.pk)
            .order_by('-published_at', '-pk')[:RELATED_POSTS_COUNT]
        )
        ctx['related_posts'] = list(related)
        return ctx
