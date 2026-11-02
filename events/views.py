from collections import namedtuple

from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from eventlandings.models import EventLanding

from .models import Event


EVENTS_PER_PAGE = 9
RELATED_EVENTS_COUNT = 3

# Элемент смешанной ленты: kind — 'landing' (лендинг события) | 'news' (новость события).
FeedItem = namedtuple('FeedItem', 'kind sort_dt obj')


class EventListView(ListView):
    """Лента «Мероприятия»: новости событий (`events.Event`) и лендинги событий
    (`eventlandings.EventLanding`) одной сеткой по убыванию даты. Дата лендинга —
    начало первого дня (лендинги без дней не показываются), новости — published_at.
    Прошедшие лендинги остаются с пометкой «Состоялось», черновики скрыты."""

    template_name = 'events/list.html'
    context_object_name = 'items'
    paginate_by = EVENTS_PER_PAGE

    def get_queryset(self):
        region = self.request.region
        news = Event.objects.filter(region=region, is_published=True)
        landings = (
            EventLanding.objects
            .filter(region=region, is_published=True)
            .prefetch_related('days')
        )
        items = [FeedItem('news', e.published_at, e) for e in news]
        items += [
            FeedItem('landing', lnd.starts_at, lnd)
            for lnd in landings
            if lnd.starts_at is not None
        ]
        items.sort(key=lambda i: (i.sort_dt, i.obj.pk), reverse=True)
        return items


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
