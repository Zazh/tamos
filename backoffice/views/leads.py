"""Заявки (leads): список с фильтрами по статусу/категории/региону/поиску,
detail-страница с inline edit формой, быстрая смена статуса."""

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from feedback.models import Lead
from regions.models import Region

from ..forms import LeadEditForm
from ..shortcuts import backoffice_required, region_scoped, render_backoffice
from ._common import make_chip_url


LEADS_PER_PAGE = 25

# Статус-чипы для фильтрации списка. Пустая строка = «Все».
LEAD_STATUSES = [
    ('', 'Все'),
    (Lead.Status.NEW, 'Новые'),
    (Lead.Status.IN_PROGRESS, 'В работе'),
    (Lead.Status.DONE, 'Закрыто'),
    (Lead.Status.REJECTED, 'Отказ'),
]


@never_cache
@backoffice_required
def leads_list(request):
    base_qs = region_scoped(
        Lead.objects.select_related('region'),
        request.user,
    )

    # Счётчики по статусам считаем ПО base_qs (region-scoped, без filter).
    counts_raw = dict(base_qs.values_list('status').annotate(c=Count('id')))
    counts = {
        'all': sum(counts_raw.values()),
        Lead.Status.NEW: counts_raw.get(Lead.Status.NEW, 0),
        Lead.Status.IN_PROGRESS: counts_raw.get(Lead.Status.IN_PROGRESS, 0),
        Lead.Status.DONE: counts_raw.get(Lead.Status.DONE, 0),
        Lead.Status.REJECTED: counts_raw.get(Lead.Status.REJECTED, 0),
    }

    qs = base_qs

    status = request.GET.get('status', '').strip()
    if status in {Lead.Status.NEW, Lead.Status.IN_PROGRESS, Lead.Status.DONE, Lead.Status.REJECTED}:
        qs = qs.filter(status=status)

    category = request.GET.get('category', '').strip()
    if category in {c for c, _ in Lead.Category.choices}:
        qs = qs.filter(category=category)

    region_slug = request.GET.get('region', '').strip()
    if region_slug and request.user.is_superuser:
        qs = qs.filter(region__slug=region_slug)

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(phone__icontains=q)
            | Q(origin__icontains=q)
            | Q(title__icontains=q)
            | Q(city__icontains=q)
            | Q(manager_note__icontains=q)
        )

    paginator = Paginator(qs, LEADS_PER_PAGE)
    page = paginator.get_page(request.GET.get('page'))

    qs_dict = request.GET.copy()
    qs_dict.pop('page', None)
    base_qs_str = qs_dict.urlencode()

    # Чипы leads_list ссылаются на свой URL целиком (а не на `?...`), потому
    # что используются в boBatchActions с full-URL navigation. Поэтому здесь
    # `make_chip_url` оборачивается с base = reverse('leads_list').
    base = reverse('backoffice:leads_list')

    status_chips = [
        {
            'code': code,
            'label': label,
            'count': counts['all'] if code == '' else counts.get(code, 0),
            'active': status == code,
            'url': _full_chip_url(request, base, code),
        }
        for code, label in LEAD_STATUSES
    ]

    return render_backoffice(
        request,
        'backoffice/leads/list.html',
        active='leads',
        page_title='Заявки',
        context={
            'page': page,
            'paginator': paginator,
            'status_chips': status_chips,
            'categories': Lead.Category.choices,
            'all_regions': Region.objects.filter(is_active=True) if request.user.is_superuser else None,
            'filters': {
                'status': status,
                'category': category,
                'region': region_slug,
                'q': q,
            },
            'base_qs': base_qs_str,
        },
    )


def _full_chip_url(request, base, status_value):
    """leads_list использует абсолютные ссылки (`/backoffice/leads/?...`)
    в отличие от blog/events где `?...`. Здесь обёртка с base."""
    relative = make_chip_url(request, status_value=status_value)
    if relative == '?':
        return base
    return f'{base}{relative}'


@never_cache
@backoffice_required
def lead_detail(request, pk):
    qs = region_scoped(Lead.objects.select_related('region'), request.user)
    lead = get_object_or_404(qs, pk=pk)

    if request.method == 'POST':
        form = LeadEditForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, 'Заявка обновлена.')
            return redirect('backoffice:lead_detail', pk=lead.pk)
    else:
        form = LeadEditForm(instance=lead)

    return render_backoffice(
        request,
        'backoffice/leads/detail.html',
        active='leads',
        page_title=f'Заявка #{lead.pk}',
        context={
            'lead': lead,
            'form': form,
            'STATUS': Lead.Status,
        },
    )


@require_POST
@backoffice_required
def lead_quick_status(request, pk):
    qs = region_scoped(Lead.objects.all(), request.user)
    lead = get_object_or_404(qs, pk=pk)

    new_status = request.POST.get('status', '')
    valid = {c for c, _ in Lead.Status.choices}
    if new_status not in valid:
        messages.error(request, 'Неизвестный статус.')
    elif lead.status == new_status:
        messages.info(request, 'Статус не изменился.')
    else:
        lead.status = new_status
        lead.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Статус: {lead.get_status_display()}.')

    next_url = request.POST.get('next') or reverse('backoffice:lead_detail', kwargs={'pk': lead.pk})
    return redirect(next_url)
