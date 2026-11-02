from django.db.models import Prefetch
from django.views.generic import DetailView

from core.gallery import strict_zip_arrange
from pages.models import HomePage

from .models import EventLanding, EventLandingDay

UPCOMING_COUNT = 3


def _published(region):
    return EventLanding.objects.filter(region=region, is_published=True)


def upcoming_landings(region, exclude_pk=None, limit=UPCOMING_COUNT):
    """Опубликованные лендинги региона с днями, ещё не прошедшие, по дате начала."""
    qs = _published(region).prefetch_related('days')
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    items = [lnd for lnd in qs if lnd.starts_at is not None and not lnd.is_past]
    items.sort(key=lambda lnd: lnd.starts_at)
    return items[:limit]


def program_columns(days):
    """Колонки таймлайна: многодневное — колонка на день (с подписью);
    однодневное — строки делятся на две колонки без подписи (как в Figma)."""
    if len(days) > 1:
        return [{'day': day, 'rows': list(day.rows.all())} for day in days]
    if not days:
        return []
    rows = list(days[0].rows.all())
    half = (len(rows) + 1) // 2
    return [c for c in ({'day': None, 'rows': rows[:half]}, {'day': None, 'rows': rows[half:]}) if c['rows']]


class EventLandingDetailView(DetailView):
    template_name = 'eventlandings/detail.html'
    context_object_name = 'landing'

    def get_queryset(self):
        return _published(self.request.region).prefetch_related(
            Prefetch('days', queryset=EventLandingDay.objects.prefetch_related('rows')),
            'materials',
            'tiles',
            'gallery',
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        landing = self.object
        home = HomePage.objects.filter(region=self.request.region).first()
        days = list(landing.days.all())

        gallery = strict_zip_arrange(landing.gallery.all())
        if not gallery and home is not None:
            gallery = strict_zip_arrange(home.gallery.all())  # Р-13: фолбэк на главную

        ctx.update({
            'home': home,
            'days': days,
            'program_columns': program_columns(days),
            'program_blocks': sum(1 for d in days for r in d.rows.all() if not r.is_break),
            'leaders': list(landing.leaders_published),
            'gallery': gallery,
            'upcoming': upcoming_landings(self.request.region, exclude_pk=landing.pk),
            'is_past': landing.is_past,
        })
        return ctx
