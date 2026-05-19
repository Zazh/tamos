"""Activities: catalog региона = list collapsible-аккордеонов с inline-формой
Activity; group edit = отдельная страница с ScheduleSlot inline.

Тренер хранится строкой на ActivityGroup (`teacher_name/teacher_phone/
teacher_bio`); отдельной модели Teacher нет.
"""

import json

from django.contrib import messages
from django.db.models import Count, Max
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from activities.models import Activity, ActivityGroup, ActivitySection
from regions.models import Region

from ...forms import (
    ACTIVITY_TRANSLATABLE,
    ActivityEditForm,
    ActivityGroupForm,
    ScheduleSlotFormSet,
    TRANSLATION_LANGS,
)
from ...shortcuts import backoffice_required, region_scoped, render_backoffice
from .._common import get_for_user_or_404, run_translate


def _get_region_for_user(request, region_pk):
    """region-scoped Region или 404. Менеджер видит только свой регион."""
    region = get_object_or_404(Region.objects.filter(is_active=True), pk=region_pk)
    if request.user.is_superuser:
        return region
    if getattr(request.user, 'manager_region_id', None) == region.pk:
        return region
    raise Http404()


def _get_activity_for_user(request, pk):
    return get_for_user_or_404(
        Activity.objects.select_related('region', 'section'), request, pk,
    )


def _get_group_for_user(request, gpk):
    """ActivityGroup, фильтрованная через activity__region."""
    return get_for_user_or_404(
        ActivityGroup.objects.select_related('activity__region', 'activity__section'),
        request,
        gpk,
        region_field='activity__region',
    )


@never_cache
@backoffice_required
def content_activities_list(request):
    """Таблица регионов со счётчиком activities."""
    regions = (
        Region.objects.filter(is_active=True)
        .annotate(activity_count=Count('activities', distinct=True))
        .order_by('name')
    )
    if not request.user.is_superuser:
        if getattr(request.user, 'manager_region_id', None):
            regions = regions.filter(pk=request.user.manager_region_id)
        else:
            regions = regions.none()

    return render_backoffice(
        request,
        'backoffice/content/activities/list.html',
        active='activities',
        page_title='Активности',
        context={'rows': list(regions)},
    )


@never_cache
@backoffice_required
def content_activities_region(request, region_pk):
    """Catalog кружков региона по секциям. Каждый кружок — collapsible-аккордеон
    с inline-формой ActivityEditForm и списком ссылок на группы.

    Сохранение каждого кружка — отдельный POST на content_activities_save
    (не один общий submit на всю страницу).
    """
    region = _get_region_for_user(request, region_pk)

    activities = list(
        Activity.objects
        .filter(region=region)
        .select_related('section')
        .prefetch_related('groups__schedule_slots')
        .order_by('section__order', 'order', 'name')
    )

    sections = list(ActivitySection.objects.order_by('order', 'slug'))
    by_section = {s.pk: [] for s in sections}
    for a in activities:
        by_section[a.section_id].append(a)

    activity_forms = {
        a.pk: ActivityEditForm(instance=a, prefix=f'a{a.pk}')
        for a in activities
    }

    buckets = [
        {'section': s, 'activities': by_section.get(s.pk, [])}
        for s in sections
    ]

    return render_backoffice(
        request,
        'backoffice/content/activities/region.html',
        active='activities',
        page_title=f'Активности — {region.name}',
        context={
            'region': region,
            'buckets': buckets,
            'sections': sections,
            'activity_forms': activity_forms,
            'activity_count': len(activities),
            'translation_langs': TRANSLATION_LANGS,
            'translatable_bases_json': json.dumps(list(ACTIVITY_TRANSLATABLE)),
        },
    )


@require_POST
@backoffice_required
def content_activities_save(request, pk):
    """POST save одного кружка из аккордеона. После save — редирект на catalog."""
    activity = _get_activity_for_user(request, pk)
    form = ActivityEditForm(request.POST, instance=activity, prefix=f'a{activity.pk}')
    if form.is_valid():
        form.save()
        messages.success(request, f'Кружок «{activity.name}» сохранён.')
    else:
        err_msg = '; '.join(
            f'{name}: {", ".join(errs)}' for name, errs in form.errors.items()
        )[:300]
        messages.error(request, f'Ошибки в форме кружка #{activity.pk}: {err_msg}')

    url = reverse('backoffice:content_activities_region', kwargs={'region_pk': activity.region_id})
    return redirect(f'{url}#activity-{activity.pk}')


@require_POST
@backoffice_required
def content_activities_activity_add(request, region_pk):
    """POST: создать пустую Activity в регионе+секции, редирект на catalog с anchor."""
    region = _get_region_for_user(request, region_pk)
    section_pk = request.POST.get('section', '').strip()
    try:
        section = ActivitySection.objects.get(pk=int(section_pk))
    except (ValueError, ActivitySection.DoesNotExist):
        messages.error(request, 'Не указана секция.')
        return redirect('backoffice:content_activities_region', region_pk=region.pk)

    max_order = (
        Activity.objects.filter(region=region, section=section)
        .aggregate(_m=Max('order'))['_m'] or 0
    )
    activity = Activity.objects.create(
        region=region,
        section=section,
        name='Новый кружок',
        name_ru='Новый кружок',
        order=max_order + 10,
        is_published=False,
    )
    messages.success(request, 'Кружок создан. Заполни поля и сохрани.')
    url = reverse('backoffice:content_activities_region', kwargs={'region_pk': region.pk})
    return redirect(f'{url}#activity-{activity.pk}')


@require_POST
@backoffice_required
def content_activities_activity_delete(request, pk):
    activity = _get_activity_for_user(request, pk)
    region_pk = activity.region_id
    name = activity.name
    activity.delete()
    messages.success(request, f'Кружок «{name}» удалён.')
    return redirect('backoffice:content_activities_region', region_pk=region_pk)


@require_POST
@backoffice_required
def content_activities_reorder(request, region_pk):
    """AJAX: сохранить DnD-порядок activities внутри секции."""
    region = _get_region_for_user(request, region_pk)
    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        section_pk = int(payload.get('section_pk') or 0)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid section_pk'}, status=400)

    order = payload.get('order') or []
    if not isinstance(order, list):
        return JsonResponse({'error': 'order must be a list'}, status=400)

    own_ids = set(
        Activity.objects.filter(region=region, section_id=section_pk)
        .values_list('pk', flat=True)
    )
    safe_order = [int(p) for p in order if int(p) in own_ids]
    for i, pk_ in enumerate(safe_order):
        Activity.objects.filter(pk=pk_).update(order=i * 10)
    return JsonResponse({'ok': True})


@require_POST
@backoffice_required
def content_activities_translate(request, pk):
    _get_activity_for_user(request, pk)
    return run_translate(request)


# ----- Group edit (отдельная страница, ScheduleSlot inline) ----------------


@require_POST
@backoffice_required
def content_activities_group_add(request, pk):
    """POST: создать пустую группу для Activity, редирект на edit Group."""
    activity = _get_activity_for_user(request, pk)
    max_order = (
        ActivityGroup.objects.filter(activity=activity).aggregate(_m=Max('order'))['_m'] or 0
    )
    group = ActivityGroup.objects.create(activity=activity, order=max_order + 10)
    messages.success(request, 'Группа создана. Задай классы, цену и расписание.')
    return redirect('backoffice:content_activities_group_edit', gpk=group.pk)


@never_cache
@backoffice_required
def content_activities_group_edit(request, gpk):
    """Edit одной группы + inline ScheduleSlot formset."""
    group = _get_group_for_user(request, gpk)
    activity = group.activity

    if request.method == 'POST':
        form = ActivityGroupForm(request.POST, instance=group)
        slot_fs = ScheduleSlotFormSet(request.POST, instance=group, prefix='slots')
        if form.is_valid() and slot_fs.is_valid():
            form.save()
            slot_fs.save()
            messages.success(request, 'Группа сохранена.')
            return redirect('backoffice:content_activities_group_edit', gpk=group.pk)
    else:
        form = ActivityGroupForm(instance=group)
        slot_fs = ScheduleSlotFormSet(instance=group, prefix='slots')

    return render_backoffice(
        request,
        'backoffice/content/activities/group_edit.html',
        active='activities',
        page_title=f'Группа · {activity.name}',
        context={
            'group': group,
            'activity': activity,
            'region': activity.region,
            'form': form,
            'slot_fs': slot_fs,
            'translation_langs': TRANSLATION_LANGS,
        },
    )


@require_POST
@backoffice_required
def content_activities_group_translate(request, gpk):
    _get_group_for_user(request, gpk)
    return run_translate(request)


@require_POST
@backoffice_required
def content_activities_group_delete(request, gpk):
    group = _get_group_for_user(request, gpk)
    activity = group.activity
    label = group.label_display or f'Группа #{group.pk}'
    group.delete()
    messages.success(request, f'Группа «{label}» удалена.')
    url = reverse('backoffice:content_activities_region', kwargs={'region_pk': activity.region_id})
    return redirect(f'{url}#activity-{activity.pk}')
