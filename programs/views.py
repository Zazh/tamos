from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from activities.models import Activity, ActivityGroup, ScheduleSlot

from .models import ProgramPage


class ProgramView(TemplateView):
    template_name = 'programs/detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        program = get_object_or_404(ProgramPage, region=self.request.region)
        ctx['program'] = program
        ctx['audience_items'] = list(program.audience_items.all())
        ctx['benefit_items'] = list(program.benefit_items.all())
        ctx['variant_cards'] = list(program.variant_cards.all())
        ctx['team_members'] = list(program.team_members.all())
        ctx['certificate_features'] = list(program.certificate_features.all())
        ctx['stats'] = list(program.stats.all())
        ctx['faq_items'] = list(program.faq_items.all())

        # Внеклассные = featured-активности текущего региона. Один источник
        # правды — activities.Activity; админка ставит галочку is_featured.
        slots_qs = ScheduleSlot.objects.order_by('order', 'pk')
        groups_qs = (
            ActivityGroup.objects
            .order_by('order', 'pk')
            .prefetch_related(Prefetch('schedule_slots', queryset=slots_qs))
        )
        ctx['featured_activities'] = list(
            Activity.objects
            .filter(region=self.request.region, is_featured=True, is_published=True)
            .select_related('section', 'teacher')
            .prefetch_related(Prefetch('groups', queryset=groups_qs))
            .order_by('section__order', 'order', 'name')
        )
        return ctx
