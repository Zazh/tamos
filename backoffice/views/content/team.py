"""Team: region-list (карточки регионов) → region-page (Featured + Other с
DnD) → create/edit per member + AI translate/SEO."""

import json

from django.contrib import messages
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from regions.models import Region
from team.models import TeamMember

from ...forms import (
    TEAM_MEMBER_OUT_OF_FORM_BASES,
    TEAM_MEMBER_TRANSLATABLE,
    TeamMemberEditForm,
    TRANSLATION_LANGS,
)
from ...shortcuts import backoffice_required, region_scoped, render_backoffice
from .._common import (
    auto_slug,
    get_for_user_or_404,
    make_blank_step,
    make_step,
    run_seo,
    run_translate,
)


TEAM_MEMBERS_PER_PAGE = 24


def _auto_slug_for_team(name):
    return auto_slug(name, model=TeamMember, prefix='member')


def _get_team_member_for_user(request, pk):
    return get_for_user_or_404(TeamMember.objects.select_related('region'), request, pk)


def _get_region_for_user(request, region_pk):
    region = get_object_or_404(Region.objects.filter(is_active=True), pk=region_pk)
    if request.user.is_superuser:
        return region
    if getattr(request.user, 'manager_region_id', None) == region.pk:
        return region
    raise Http404()


def _teammember_steps(member):
    ru_fields = ['name_ru', 'role_ru', 'photo']
    kk_fields = ['name_kk', 'role_kk']
    en_fields = ['name_en', 'role_en']
    seo_fields = ['seo_title_ru', 'seo_description_ru', 'og_title_ru', 'og_image']
    pub_fields = ['is_published', 'is_featured']

    return [
        make_step(member, id='ru', label='Основа (RU)', fields=ru_fields, required=True),
        make_step(member, id='kk', label='Перевод KZ', fields=kk_fields),
        make_step(member, id='en', label='Перевод EN', fields=en_fields),
        make_step(member, id='seo', label='SEO', fields=seo_fields),
        make_step(member, id='publish', label='Публикация', fields=pub_fields),
    ]


def _teammember_steps_for_create():
    return [
        make_blank_step(id='ru', label='Основа (RU)', total=3, required=True),
        make_blank_step(id='kk', label='Перевод KZ', total=2),
        make_blank_step(id='en', label='Перевод EN', total=2),
        make_blank_step(id='seo', label='SEO', total=4),
        make_blank_step(id='publish', label='Публикация', total=2),
    ]


@never_cache
@backoffice_required
def content_team_list(request):
    """Карточки регионов со счётчиком членов команды (паттерн activities-list).

    Менеджер региона видит только свой регион; если регион один — сразу
    редиректит в `content_team_region`. Su видит все активные регионы.
    """
    regions = (
        Region.objects.filter(is_active=True)
        .annotate(
            member_count=Count('team_members', distinct=True),
            featured_count=Count(
                'team_members',
                filter=Q(team_members__is_featured=True, team_members__is_published=True),
                distinct=True,
            ),
        )
        .order_by('name')
    )
    if not request.user.is_superuser:
        if getattr(request.user, 'manager_region_id', None):
            regions = regions.filter(pk=request.user.manager_region_id)
        else:
            regions = regions.none()

    rows = list(regions)
    if len(rows) == 1 and not request.user.is_superuser:
        return redirect('backoffice:content_team_region', region_pk=rows[0].pk)

    return render_backoffice(
        request,
        'backoffice/content/team/list.html',
        active='team',
        page_title='Команда',
        context={'rows': rows},
    )


@never_cache
@backoffice_required
def content_team_region(request, region_pk):
    """Команда одного региона. Две секции: «Избранные» (попадают на лендинг
    «Программа») сверху и «Остальные» — снизу. DnD-сортировка через
    `content_team_reorder` (AJAX)."""
    region = _get_region_for_user(request, region_pk)

    base_qs = (
        TeamMember.objects
        .filter(region=region)
        .order_by('order', 'pk')
    )
    featured = list(base_qs.filter(is_featured=True))
    rest = list(base_qs.filter(is_featured=False))

    return render_backoffice(
        request,
        'backoffice/content/team/region.html',
        active='team',
        page_title=f'Команда · {region.name}',
        context={
            'region': region,
            'featured_members': featured,
            'other_members': rest,
            'all_regions': (
                Region.objects.filter(is_active=True).order_by('name')
                if request.user.is_superuser else None
            ),
        },
    )


@require_POST
@backoffice_required
def content_team_reorder(request, region_pk):
    """AJAX: сохранить DnD-порядок TeamMember одной группы внутри региона.

    Body: `{"group": "featured" | "other", "order": [pk1, pk2, ...]}`.
    Order пишется как `i*10`. Group — safety-фильтр, сам флаг `is_featured`
    НЕ меняется этим endpoint'ом.
    """
    region = _get_region_for_user(request, region_pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    group = str(payload.get('group') or '').strip()
    if group not in {'featured', 'other'}:
        return JsonResponse({'error': 'group must be featured|other'}, status=400)

    order = payload.get('order') or []
    if not isinstance(order, list):
        return JsonResponse({'error': 'order must be a list'}, status=400)

    own_ids = set(
        TeamMember.objects
        .filter(region=region, is_featured=(group == 'featured'))
        .values_list('pk', flat=True)
    )
    safe_order = [int(p) for p in order if int(p) in own_ids]
    for i, pk_ in enumerate(safe_order):
        TeamMember.objects.filter(pk=pk_).update(order=i * 10)
    return JsonResponse({'ok': True})


@never_cache
@backoffice_required
@require_http_methods(['GET', 'POST'])
def content_team_create(request):
    if request.method == 'POST':
        form = TeamMemberEditForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            member = form.save(commit=False)
            name = form.cleaned_data.get('name_ru') or member.name or 'Без имени'
            member.slug = _auto_slug_for_team(name)
            member.is_published = bool(request.POST.get('publish_now'))
            member.save()
            form.save_m2m()
            messages.success(
                request,
                f'{"Опубликован" if member.is_published else "Сохранён черновик"} «{member.name}».',
            )
            return redirect('backoffice:content_team_edit', pk=member.pk)
    else:
        form = TeamMemberEditForm(user=request.user)

    return render_backoffice(
        request,
        'backoffice/content/team/create.html',
        active='team',
        page_title='Новый член команды',
        context={
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(_teammember_steps_for_create()),
            'translatable_bases_json': json.dumps(list(TEAM_MEMBER_TRANSLATABLE)),
            'out_of_form_bases': TEAM_MEMBER_OUT_OF_FORM_BASES,
        },
    )


@never_cache
@backoffice_required
def content_team_edit(request, pk):
    member = _get_team_member_for_user(request, pk)
    # ModelForm мутирует instance — сохраняем оригиналы slug/region_id ДО init.
    original_slug = member.slug
    original_region_id = member.region_id

    if request.method == 'POST':
        form = TeamMemberEditForm(
            request.POST, request.FILES, instance=member, user=request.user,
        )
        if form.is_valid():
            saved = form.save(commit=False)
            saved.region_id = original_region_id
            if not saved.slug:
                saved.slug = original_slug
            saved.save()
            form.save_m2m()
            messages.success(request, 'Изменения сохранены.')
            return redirect('backoffice:content_team_edit', pk=saved.pk)
    else:
        form = TeamMemberEditForm(instance=member, user=request.user)

    return render_backoffice(
        request,
        'backoffice/content/team/edit.html',
        active='team',
        page_title=f'Команда · {member.name or "Без имени"}',
        context={
            'member': member,
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(_teammember_steps(member)),
            'translatable_bases_json': json.dumps(list(TEAM_MEMBER_TRANSLATABLE)),
            'out_of_form_bases': TEAM_MEMBER_OUT_OF_FORM_BASES,
            'team_translate_url': reverse('backoffice:content_team_translate', kwargs={'pk': member.pk}),
            'team_seo_url': reverse('backoffice:content_team_seo', kwargs={'pk': member.pk}),
        },
    )


@require_POST
@backoffice_required
def content_team_delete(request, pk):
    member = _get_team_member_for_user(request, pk)
    name = member.name or f'Член команды #{member.pk}'
    member.delete()
    messages.success(request, f'«{name}» удалён.')
    return redirect('backoffice:content_team_list')


@require_POST
@backoffice_required
def content_team_seo(request, pk):
    _get_team_member_for_user(request, pk)
    return run_seo(request, empty_hint='Заполни имя и должность на RU.')


@require_POST
@backoffice_required
def content_team_translate(request, pk):
    _get_team_member_for_user(request, pk)
    return run_translate(request)
