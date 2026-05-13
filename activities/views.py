from django.db.models import Prefetch
from django.views.generic import TemplateView

from .models import Activity, ActivityGroup, ActivitySection, ScheduleSlot


class ActivitiesListView(TemplateView):
    template_name = 'activities/list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        region = self.request.region

        slots_qs = ScheduleSlot.objects.order_by('order', 'pk')
        groups_qs = (
            ActivityGroup.objects
            .order_by('order', 'pk')
            .prefetch_related(Prefetch('schedule_slots', queryset=slots_qs))
        )
        activities_qs = (
            Activity.objects
            .filter(region=region, is_published=True)
            .select_related('teacher', 'section')
            .prefetch_related(Prefetch('groups', queryset=groups_qs))
            .order_by('order', 'name')
        )

        sections = list(ActivitySection.objects.order_by('order', 'slug'))
        activities_by_section = {s.pk: [] for s in sections}
        for activity in activities_qs:
            bucket = activities_by_section.get(activity.section_id)
            if bucket is not None:
                bucket.append(activity)

        ctx['sections'] = [
            {'section': s, 'activities': activities_by_section[s.pk]}
            for s in sections
            if activities_by_section[s.pk]
        ]

        # Для dropdown «Класс»: 1..11. Просто range, не выводим из БД —
        # школьные классы в Казахстане строго 1–11.
        ctx['grades_range'] = list(range(1, 12))
        # Для dropdown «День недели»: 5 рабочих дней. На входе пары
        # (key, full_label) — переводы лежат в models.py choices.
        ctx['weekdays'] = list(ScheduleSlot.Day.choices)[:5]  # Пн..Пт, без сб/вс
        return ctx
