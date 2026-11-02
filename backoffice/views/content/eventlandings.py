"""Мероприятия (лендинги событий `eventlandings`): список/create/edit/delete +
AI translate/SEO, inline дни/материалы/плитки, страница дня (программа),
AJAX-галерея карусели «Школа».

Клон events (lazy-draft, slug из title на первом сохранении); вместо Trix и
обложки — тексты лендинга, стоимость и ведущие из «Команды». Страница дня —
как группа активностей, галерея — как на Главной (strict-zip при upload).
"""

import json
import secrets

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import translation
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from core.gallery import strict_zip_arrange
from core.image_optimize import normalize_uploaded_image
from eventlandings.models import EventLanding, EventLandingDay, EventLandingGalleryImage
from regions.models import Region

from ...forms import (
    EVENTLANDING_OUT_OF_FORM_BASES,
    EVENTLANDING_TRANSLATABLE,
    EventLandingDayFormSet,
    EventLandingEditForm,
    EventLandingMaterialFormSet,
    EventLandingProgramRowFormSet,
    EventLandingTileFormSet,
    TRANSLATION_LANGS,
)
from ...shortcuts import backoffice_required, region_scoped, render_backoffice
from .._common import (
    append_to_gallery,
    apply_safe_reorder,
    auto_slug,
    get_for_user_or_404,
    make_published_chips,
    make_readonly_step,
    make_step,
    parse_json_body,
    run_seo,
    run_translate,
    serialize_gallery_image,
    update_gallery_image_translations,
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


def _landing_formsets(landing, data=None):
    """Inline-formset'ы основной формы: (label для ошибок, formset)."""
    days_qs = landing.days.annotate(rows_count=Count('rows'))
    return [
        ('Дни', EventLandingDayFormSet(data, instance=landing, prefix='days', queryset=days_qs)),
        ('Материалы', EventLandingMaterialFormSet(data, instance=landing, prefix='materials')),
        ('Плитки', EventLandingTileFormSet(data, instance=landing, prefix='tiles')),
    ]


def _formset_errors(labelled_formsets):
    """Ошибки formset'ов одним списком «Дни · строка 2 · Окончание: …» — для вывода
    сверху формы (карточки могут быть свёрнуты)."""
    out = []
    for label, fs in labelled_formsets:
        out.extend(f'{label}: {err}' for err in fs.non_form_errors())
        for i, f in enumerate(fs.forms, start=1):
            for name, errs in f.errors.items():
                field = f.fields.get(name)
                field_label = f' · {field.label}' if field is not None else ''
                out.extend(f'{label} · строка {i}{field_label}: {err}' for err in errs)
    return out


def _serialize_gallery_item(img):
    """Как serialize_gallery_image + orientation (бейдж слота в boGallery)."""
    return {**serialize_gallery_image(img, locale_bases=('alt_text',)), 'orientation': img.orientation}


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
        formsets = _landing_formsets(landing, request.POST)
        # Список, не генератор: валидируем всё сразу, чтобы показать все ошибки.
        if all([form.is_valid()] + [fs.is_valid() for _, fs in formsets]):
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
                for _, fs in formsets:
                    fs.save()
            messages.success(request, 'Мероприятие сохранено.')
            return redirect('backoffice:content_eventlandings_edit', pk=saved.pk)
    else:
        form = EventLandingEditForm(instance=landing, user=request.user)
        formsets = _landing_formsets(landing)

    site_urls = {lang: _site_url(landing, lang) for lang in TRANSLATION_LANGS} \
        if landing.is_published else {}
    gallery_items = [_serialize_gallery_item(img) for img in landing.gallery.all()]

    return render_backoffice(
        request,
        'backoffice/content/eventlandings/edit.html',
        active='eventlandings',
        page_title=f'Мероприятия · {landing.title or "Новое мероприятие"}',
        context={
            'landing': landing,
            'form': form,
            'day_fs': formsets[0][1],
            'material_fs': formsets[1][1],
            'tile_fs': formsets[2][1],
            'formset_errors': _formset_errors(formsets),
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(_landing_steps(landing)),
            'translatable_bases_json': json.dumps(list(EVENTLANDING_TRANSLATABLE)),
            'out_of_form_bases': EVENTLANDING_OUT_OF_FORM_BASES,
            'site_urls_json': json.dumps(site_urls),
            'translate_url': reverse('backoffice:content_eventlandings_translate', kwargs={'pk': landing.pk}),
            'seo_url': reverse('backoffice:content_eventlandings_seo', kwargs={'pk': landing.pk}),
            'gallery_items_json': json.dumps(gallery_items),
        },
    )


@never_cache
@backoffice_required
def content_eventlandings_day_edit(request, pk, dpk):
    """Программа одного дня: inline-formset строк (DnD порядок, перерывы)."""
    landing = _get_landing_for_user(request, pk)
    day = get_object_or_404(EventLandingDay, pk=dpk, landing=landing)

    if request.method == 'POST':
        row_fs = EventLandingProgramRowFormSet(request.POST, instance=day, prefix='rows')
        if row_fs.is_valid():
            with transaction.atomic():
                row_fs.save()
            messages.success(request, 'Программа дня сохранена.')
            return redirect('backoffice:content_eventlandings_day_edit', pk=landing.pk, dpk=day.pk)
    else:
        row_fs = EventLandingProgramRowFormSet(instance=day, prefix='rows')

    return render_backoffice(
        request,
        'backoffice/content/eventlandings/day_edit.html',
        active='eventlandings',
        page_title=f'Мероприятия · {landing.title or "Новое мероприятие"} · программа дня',
        context={
            'landing': landing,
            'day': day,
            'row_fs': row_fs,
            'formset_errors': _formset_errors([('Программа', row_fs)]),
            'translation_langs': TRANSLATION_LANGS,
            'translate_url': reverse('backoffice:content_eventlandings_translate', kwargs={'pk': landing.pk}),
        },
    )


@require_POST
@backoffice_required
def content_eventlandings_gallery_upload(request, pk):
    """Multi-upload фото карусели. `orientation` определяется в save() модели,
    затем весь список расставляется strict-zip-ом с шагом order 10 (как Главная)."""
    landing = _get_landing_for_user(request, pk)
    files = request.FILES.getlist('images')
    if not files:
        return JsonResponse({'error': 'No files'}, status=400)

    append_to_gallery(
        landing.gallery,
        [normalize_uploaded_image(f) for f in files],
        model=EventLandingGalleryImage,
        extra_kwargs={'landing': landing},
    )
    for i, img in enumerate(strict_zip_arrange(landing.gallery.all())):
        if img.order != i * 10:
            img.order = i * 10
            img.save(update_fields=['order'])

    return JsonResponse({'items': [_serialize_gallery_item(img) for img in landing.gallery.all()]})


@require_POST
@backoffice_required
def content_eventlandings_gallery_reorder(request, pk):
    """Порядок, заданный менеджером через DnD, — без пересортировки strict-zip."""
    landing = _get_landing_for_user(request, pk)
    payload, err = parse_json_body(request)
    if err:
        return err
    apply_safe_reorder(
        EventLandingGalleryImage,
        queryset=landing.gallery.all(),
        order_payload=list(payload.get('order') or []),
    )
    return JsonResponse({'ok': True})


@require_POST
@backoffice_required
def content_eventlandings_gallery_update(request, pk, gpk):
    landing = _get_landing_for_user(request, pk)
    img = get_object_or_404(EventLandingGalleryImage, pk=gpk, landing=landing)
    payload, err = parse_json_body(request)
    if err:
        return err
    fields = ('alt_text_ru', 'alt_text_kk', 'alt_text_en')
    max_len = EventLandingGalleryImage._meta.get_field('alt_text').max_length
    update_gallery_image_translations(
        img,
        {k: str(payload[k])[:max_len] for k in fields if k in payload},
        fields=fields,
    )
    return JsonResponse({'ok': True, 'item': _serialize_gallery_item(img)})


@require_POST
@backoffice_required
def content_eventlandings_gallery_delete(request, pk, gpk):
    landing = _get_landing_for_user(request, pk)
    get_object_or_404(EventLandingGalleryImage, pk=gpk, landing=landing).delete()
    return JsonResponse({'ok': True})


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
