from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from .models import TeamMember


# slug → имя BooleanField на TeamMember. 'admin' — флаг администрации
# (независим от уровней преподавания, член команды может попадать сразу в
# несколько chip'ов: «Старшие» и «Администрация»).
LEVEL_FIELDS = {
    'primary': 'teaches_primary',
    'middle': 'teaches_middle',
    'senior': 'teaches_senior',
    'admin': 'is_admin',
}


class TeamListView(ListView):
    """Список членов команды текущего региона. Фильтр `?level=primary|middle|
    senior|admin` по соответствующему BooleanField (см. LEVEL_FIELDS)."""

    template_name = 'team/list.html'
    context_object_name = 'members'

    def get_queryset(self):
        region = self.request.region
        qs = (
            TeamMember.objects
            .filter(region=region, is_published=True)
            # Избранные всегда сверху — внутри группы сортировка по order/pk.
            .order_by('-is_featured', 'order', 'pk')
        )
        level = self.request.GET.get('level')
        field = LEVEL_FIELDS.get(level)
        if field:
            qs = qs.filter(**{field: True})
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        region = self.request.region
        # Показываем chip только если в регионе есть хотя бы один опубликованный
        # сотрудник с этим флагом — иначе пустые кнопки.
        live = TeamMember.objects.filter(region=region, is_published=True)
        ctx['level_chips'] = [
            {'slug': 'admin',   'label': _('Администрация')},
            {'slug': 'primary', 'label': _('Младшие (1–4)')},
            {'slug': 'middle',  'label': _('Средние (5–8)')},
            {'slug': 'senior',  'label': _('Старшие (9–11)')},
        ]
        # Уберём те chip'ы, по которым в регионе никого нет.
        ctx['level_chips'] = [
            c for c in ctx['level_chips']
            if live.filter(**{LEVEL_FIELDS[c['slug']]: True}).exists()
        ]
        ctx['current_level_slug'] = self.request.GET.get('level') or ''
        return ctx


class TeamDetailView(DetailView):
    template_name = 'team/detail.html'
    context_object_name = 'member'

    def get_object(self, queryset=None):
        region = self.request.region
        return get_object_or_404(
            TeamMember.objects.filter(region=region, is_published=True),
            slug=self.kwargs['slug'],
        )
