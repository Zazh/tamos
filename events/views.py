from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from .models import Event


EVENTS_PER_PAGE = 9
RELATED_EVENTS_COUNT = 3


class EventListView(ListView):
    """Лента мероприятий. Без фильтров — плоский список по дате."""

    template_name = 'events/list.html'
    context_object_name = 'events'
    paginate_by = EVENTS_PER_PAGE

    def get_queryset(self):
        region = self.request.region
        return (
            Event.objects
            .filter(region=region, is_published=True)
            .order_by('-published_at', '-pk')
        )


class EventDetailView(DetailView):
    template_name = 'events/detail.html'
    context_object_name = 'event'

    def get_object(self, queryset=None):
        region = self.request.region
        return get_object_or_404(
            Event.objects.filter(region=region, is_published=True),
            slug=self.kwargs['slug'],
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        event = ctx['event']
        related = (
            Event.objects
            .filter(region=event.region, is_published=True)
            .exclude(pk=event.pk)
            .order_by('-published_at', '-pk')[:RELATED_EVENTS_COUNT]
        )
        ctx['related_events'] = list(related)
        return ctx
