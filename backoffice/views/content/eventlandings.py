"""Мероприятия (лендинги событий `eventlandings`): список/create/edit/delete +
AI translate/SEO.

Клон events (lazy-draft, slug из title на первом сохранении); вместо Trix и
обложки — тексты лендинга, стоимость и ведущие из «Команды».
"""

import json
import secrets

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import translation
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from eventlandings.models import EventLanding
from regions.models import Region

from ...forms import (
    EVENTLANDING_OUT_OF_FORM_BASES,
    EVENTLANDING_TRANSLATABLE,
    EventLandingEditForm,
    TRANSLATION_LANGS,
)
from ...shortcuts import backoffice_required, region_scoped, render_backoffice
from .._common import (
    auto_slug,
    get_for_user_or_404,
    make_published_chips,
    make_readonly_step,
    make_step,
    run_seo,
    run_translate,
)


EVENTLANDINGS_PER_PAGE = 20
DRAFT_SLUG_PREFIX = 'draft-'

# Обязательная основа лендинга — те же базы считают шаги переводов.
STEP_BASES = (
    'title', 'lead', 'badge_text', 'audience_title', 'goal',
    'reg_title', 'form_title', 'cta_text',
)

# auto_slug (django slugify) выбрасывает кириллицу: «Навыки XXI века» → «xxi-a3f7».
# Транслитерируем до slugify, чтобы URL лендинга был читаемым («navyki-xxi-veka-a3f7»).
_TRANSLIT = str.maketrans({
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
    'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu',
    'я': 'ya', 'ә': 'a', 'ғ': 'g', 'қ': 'k', 'ң': 'n', 'ө': 'o', 'ұ': 'u', 'ү': 'u',
    'һ': 'h', 'і': 'i',
})


def _auto_slug_for_landing(title):
    return auto_slug(title.lower().translate(_TRANSLIT), model=EventLanding, prefix='event')


def _new_draft_slug():
    for _ in range(5):
        slug = f'{DRAFT_SLUG_PREFIX}{secrets.token_hex(4)}'
        if not EventLanding.objects.filter(slug=slug).exists():
            return slug
    return f'{DRAFT_SLUG_PREFIX}{secrets.token_hex(8)}'


def _get_landing_for_user(request, pk):
    return get_for_user_or_404(EventLanding.objects.select_related('region'), request, pk)


def _site_url(landing, lang):
    with translation.override(lang):
        return reverse(
            'eventlandings:detail',
            kwargs={'region_slug': landing.region.slug, 'slug': landing.slug},
        )


def _landing_steps(landing):
    days_with_rows = landing.days.filter(rows__isnull=False).distinct().count()
    return [
        make_step(landing, id='ru', label='Основа (RU)',
                  fields=[f'{b}_ru' for b in STEP_BASES], required=True),
        make_readonly_step(id='days', label='Даты и программа',
                           filled=days_with_rows, total=landing.days.count()),
        make_step(landing, id='kk', label='Перевод KZ', fields=[f'{b}_kk' for b in STEP_BASES]),
        make_step(landing, id='en', label='Перевод EN', fields=[f'{b}_en' for b in STEP_BASES]),
        make_step(landing, id='seo', label='SEO',
                  fields=['seo_title_ru', 'seo_description_ru', 'og_title_ru']),
        make_step(landing, id='publish', label='Публикация', fields=['is_published']),
    ]


@never_cache
@backoffice_required
def content_eventlandings_list(request):
    base_qs = region_scoped(
        EventLanding.objects.select_related('region').prefetch_related('days'),
        request.user,
    )

    region_slug = request.GET.get('region', '').strip()
    q = request.GET.get('q', '').strip()

    pre_status_qs = base_qs
    if region_slug and request.user.is_superuser:
        pre_status_qs = pre_status_qs.filter(region__slug=region_slug)
    if q:
        pre_status_qs = pre_status_qs.filter(
            Q(title__icontains=q) | Q(slug__icontains=q) | Q(lead__icontains=q)
        )

    status_counts = {
        'all': pre_status_qs.count(),
        'published': pre_status_qs.filter(is_published=True).count(),
        'draft': pre_status_qs.filter(is_published=False).count(),
    }

    status = request.GET.get('status', '').strip()
    qs = pre_status_qs
    if status == 'published':
        qs = qs.filter(is_published=True)
    elif status == 'draft':
        qs = qs.filter(is_published=False)

    qs = qs.order_by('-created_at', '-pk')

    paginator = Paginator(qs, EVENTLANDINGS_PER_PAGE)
    page = paginator.get_page(request.GET.get('page'))
    for landing in page.object_list:
        landing.site_url = _site_url(landing, 'ru') if landing.is_published else ''

    qs_dict = request.GET.copy()
    qs_dict.pop('page', None)

    return render_backoffice(
        request,
        'backoffice/content/eventlandings/list.html',
        active='eventlandings',
        page_title='Мероприятия',
        context={
            'page': page,
            'paginator': paginator,
            'all_regions': Region.objects.filter(is_active=True) if request.user.is_superuser else None,
            'filters': {'status': status, 'region': region_slug, 'q': q},
            'status_chips': make_published_chips(request, counts=status_counts, active=status),
            'base_qs': qs_dict.urlencode(),
        },
    )


@require_POST
@backoffice_required
def content_eventlandings_create(request):
    """Создаёт пустой черновик и сразу редиректит на edit (lazy-draft, как events)."""
    if request.user.is_superuser:
        region = Region.objects.filter(is_active=True).order_by('-is_default', 'pk').first()
    else:
        region_id = getattr(request.user, 'manager_region_id', None)
        region = Region.objects.filter(pk=region_id).first() if region_id else None

    if region is None:
        messages.error(request, 'Не удалось определить регион. Создай регион или назначь его менеджеру.')
        return redirect('backoffice:content_eventlandings_list')

    landing = EventLanding.objects.create(
        region=region,
        slug=_new_draft_slug(),
        title='',
        is_published=False,
    )
    return redirect('backoffice:content_eventlandings_edit', pk=landing.pk)


@never_cache
@backoffice_required
def content_eventlandings_edit(request, pk):
    landing = _get_landing_for_user(request, pk)
    # ModelForm мутирует instance — сохраняем оригиналы slug/region_id ДО init.
    # См. [[feedback_modelform_mutates_instance]].
    original_slug = landing.slug
    original_region_id = landing.region_id

    if request.method == 'POST':
        form = EventLandingEditForm(request.POST, instance=landing, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                saved = form.save(commit=False)
                saved.region_id = original_region_id
                # Slug в UI не редактируется: меняется только у черновика при первом title.
                saved.slug = original_slug
                title_for_slug = (form.cleaned_data.get('title_ru') or '').strip()
                if original_slug.startswith(DRAFT_SLUG_PREFIX) and title_for_slug:
                    saved.slug = _auto_slug_for_landing(title_for_slug)
                saved.save()
                form.save_m2m()
            messages.success(request, 'Мероприятие сохранено.')
            return redirect('backoffice:content_eventlandings_edit', pk=saved.pk)
    else:
        form = EventLandingEditForm(instance=landing, user=request.user)

    site_urls = {lang: _site_url(landing, lang) for lang in TRANSLATION_LANGS} \
        if landing.is_published else {}

    return render_backoffice(
        request,
        'backoffice/content/eventlandings/edit.html',
        active='eventlandings',
        page_title=f'Мероприятия · {landing.title or "Новое мероприятие"}',
        context={
            'landing': landing,
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(_landing_steps(landing)),
            'translatable_bases_json': json.dumps(list(EVENTLANDING_TRANSLATABLE)),
            'out_of_form_bases': EVENTLANDING_OUT_OF_FORM_BASES,
            'site_urls_json': json.dumps(site_urls),
            'translate_url': reverse('backoffice:content_eventlandings_translate', kwargs={'pk': landing.pk}),
            'seo_url': reverse('backoffice:content_eventlandings_seo', kwargs={'pk': landing.pk}),
        },
    )


@require_POST
@backoffice_required
def content_eventlandings_delete(request, pk):
    landing = _get_landing_for_user(request, pk)
    title = landing.title or f'Мероприятие #{landing.pk}'
    landing.delete()
    messages.success(request, f'Мероприятие «{title}» удалено.')
    return redirect('backoffice:content_eventlandings_list')


@require_POST
@backoffice_required
def content_eventlandings_seo(request, pk):
    _get_landing_for_user(request, pk)
    return run_seo(request, empty_hint='Заполни заголовок и лид на RU.')


@require_POST
@backoffice_required
def content_eventlandings_translate(request, pk):
    _get_landing_for_user(request, pk)
    return run_translate(request)
