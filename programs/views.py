from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

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
        ctx['activity_items'] = list(program.activity_items.all())
        ctx['stats'] = list(program.stats.all())
        ctx['faq_items'] = list(program.faq_items.all())
        return ctx
