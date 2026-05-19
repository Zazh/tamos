"""AdmissionPage edit (общие тексты + 2 inline + grid 6 вариантов) +
AdmissionVariant edit (per dept × grade) + AI-translate/SEO для обоих."""

import json

from django.contrib import messages
from django.db.models import Count, Max
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from admission.models import AdmissionPage, AdmissionVariant

from ...forms import (
    ADMISSION_PAGE_INLINE_FORMSETS,
    ADMISSION_PAGE_TRANSLATABLE,
    ADMISSION_VARIANT_FIXED_SLOT_COUNT,
    ADMISSION_VARIANT_FIXED_SLOT_SECTIONS,
    ADMISSION_VARIANT_INLINE_FORMSETS,
    ADMISSION_VARIANT_TRANSLATABLE,
    AdmissionPageEditForm,
    AdmissionVariantEditForm,
    TRANSLATION_LANGS,
)
from ...shortcuts import backoffice_required, region_scoped, render_backoffice
from .._common import (
    get_for_user_or_404,
    make_readonly_step,
    make_step,
    run_seo,
    run_translate,
)


# ----- AdmissionPage --------------------------------------------------------


@never_cache
@backoffice_required
def content_admission_list(request):
    """Список AdmissionPage по регионам (1 строка для менеджера, N для superuser)."""
    qs = (
        region_scoped(AdmissionPage.objects.select_related('region'), request.user)
        .annotate(
            variant_count=Count('variants', distinct=True),
            included_count=Count('included_items', distinct=True),
            document_count=Count('documents', distinct=True),
        )
        .order_by('region__name')
    )
    return render_backoffice(
        request,
        'backoffice/content/admission/list.html',
        active='admission',
        page_title='Поступление',
        context={'rows': qs},
    )


def _get_admission_for_user(request, pk):
    return get_for_user_or_404(AdmissionPage.objects.all(), request, pk)


def _get_admission_variant_for_user(request, vpk):
    """region-scoped AdmissionVariant через page__region (region — FK на странице)."""
    return get_for_user_or_404(
        AdmissionVariant.objects.select_related('page__region', 'department', 'grade'),
        request,
        vpk,
        region_field='page__region',
    )


def _admissionpage_steps(page):
    ru_fields = [
        'stage_consultation_title_ru', 'stage_testing_title_ru',
        'stage_result_title_ru', 'stage_contract_title_ru', 'stage_enrollment_title_ru',
        'testing_section_title_ru', 'result_section_title_ru',
        'contract_section_title_ru', 'enrollment_section_title_ru', 'consultation_section_title_ru',
        'testing_rules_text_ru', 'testing_price_value_ru',
        'enrollment_lead_ru', 'consultation_lead_ru',
    ]
    kk_fields = [f.replace('_ru', '_kk') for f in ru_fields]
    en_fields = [f.replace('_ru', '_en') for f in ru_fields]

    inline_total = page.included_items.count() + page.documents.count()
    return [
        make_step(page, id='ru', label='Основа (RU)', fields=ru_fields, required=True),
        make_step(page, id='kk', label='Перевод KZ', fields=kk_fields),
        make_step(page, id='en', label='Перевод EN', fields=en_fields),
        make_readonly_step(id='inline', label='Списки', filled=inline_total, total=inline_total),
    ]


@never_cache
@backoffice_required
def content_admission_edit(request, pk):
    page = _get_admission_for_user(request, pk)

    if request.method == 'POST':
        form = AdmissionPageEditForm(request.POST, instance=page)
        formsets = [
            (prefix, fs_cls(request.POST, instance=page, prefix=prefix), related_name, label, bases)
            for prefix, fs_cls, related_name, label, bases in ADMISSION_PAGE_INLINE_FORMSETS
        ]
        all_valid = form.is_valid() and all(fs.is_valid() for _, fs, *_ in formsets)
        if all_valid:
            form.save()
            for _, fs, *_ in formsets:
                fs.save()
            messages.success(request, 'Страница «Поступление» сохранена.')
            return redirect('backoffice:content_admission_edit', pk=page.pk)
    else:
        form = AdmissionPageEditForm(instance=page)
        formsets = [
            (prefix, fs_cls(instance=page, prefix=prefix), related_name, label, bases)
            for prefix, fs_cls, related_name, label, bases in ADMISSION_PAGE_INLINE_FORMSETS
        ]

    # Превью 6 вариантов с счётчиком заполненности.
    variants = list(
        page.variants
        .select_related('department', 'grade')
        .annotate(
            testing_count=Count('testing_features', distinct=True),
            pricing_count=Count('pricing_plans', distinct=True),
        )
        .order_by('department__order', 'grade__order')
    )
    variants_with_status = [
        {
            'pk': v.pk,
            'department': v.department,
            'grade': v.grade,
            'h1': v.h1,
            'is_filled': bool(
                (v.hero_lead or '').strip()
                and (v.testing_lead or '').strip()
                and (v.pricing_lead or '').strip()
            ),
            'testing_count': v.testing_count,
            'pricing_count': v.pricing_count,
        }
        for v in variants
    ]

    steps = _admissionpage_steps(page)

    return render_backoffice(
        request,
        'backoffice/content/admission/page_edit.html',
        active='admission',
        page_title=f'Поступление — {page.region.name}',
        context={
            'page': page,
            'form': form,
            'formsets': formsets,
            'variants': variants_with_status,
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(steps),
            'translatable_bases_json': json.dumps(list(ADMISSION_PAGE_TRANSLATABLE)),
            'admission_translate_url': reverse('backoffice:content_admission_translate', kwargs={'pk': page.pk}),
        },
    )


@require_POST
@backoffice_required
def content_admission_translate(request, pk):
    _get_admission_for_user(request, pk)
    return run_translate(request)


# ----- AdmissionVariant ----------------------------------------------------


def _ensure_admission_fixed_sections(variant):
    """Гарантирует 4 testing_features на variant (аналог `_ensure_program_fixed_sections`)."""
    for related_name, model in ADMISSION_VARIANT_FIXED_SLOT_SECTIONS:
        qs = getattr(variant, related_name)
        existing = qs.count()
        if existing >= ADMISSION_VARIANT_FIXED_SLOT_COUNT:
            continue
        max_order = qs.aggregate(_m=Max('order'))['_m'] or 0
        for i in range(ADMISSION_VARIANT_FIXED_SLOT_COUNT - existing):
            model.objects.create(
                variant=variant,
                order=max_order + (i + 1) * 10,
            )


def _admissionvariant_steps(variant):
    ru_fields = [
        'h1_ru', 'hero_lead_ru',
        'testing_lead_ru', 'result_intro_ru', 'result_detail_ru', 'pricing_lead_ru',
    ]
    kk_fields = [f.replace('_ru', '_kk') for f in ru_fields]
    en_fields = [f.replace('_ru', '_en') for f in ru_fields]
    seo_fields = ['seo_title_ru', 'seo_description_ru', 'og_title_ru', 'og_description_ru']

    inline_total = variant.testing_features.count() + variant.pricing_plans.count()
    return [
        make_step(variant, id='ru', label='Основа (RU)', fields=ru_fields, required=True),
        make_step(variant, id='kk', label='Перевод KZ', fields=kk_fields),
        make_step(variant, id='en', label='Перевод EN', fields=en_fields),
        make_step(variant, id='seo', label='SEO', fields=seo_fields),
        make_readonly_step(id='inline', label='Карточки', filled=inline_total, total=inline_total),
    ]


@never_cache
@backoffice_required
def content_admission_variant_edit(request, vpk):
    variant = _get_admission_variant_for_user(request, vpk)

    _ensure_admission_fixed_sections(variant)

    if request.method == 'POST':
        form = AdmissionVariantEditForm(request.POST, request.FILES, instance=variant)
        formsets = [
            (prefix, fs_cls(request.POST, request.FILES, instance=variant, prefix=prefix), related_name, label, bases)
            for prefix, fs_cls, related_name, label, bases in ADMISSION_VARIANT_INLINE_FORMSETS
        ]
        all_valid = form.is_valid() and all(fs.is_valid() for _, fs, *_ in formsets)
        if all_valid:
            form.save()
            for _, fs, *_ in formsets:
                fs.save()
            messages.success(request, 'Вариант страницы сохранён.')
            return redirect('backoffice:content_admission_variant_edit', vpk=variant.pk)
    else:
        form = AdmissionVariantEditForm(instance=variant)
        formsets = [
            (prefix, fs_cls(instance=variant, prefix=prefix), related_name, label, bases)
            for prefix, fs_cls, related_name, label, bases in ADMISSION_VARIANT_INLINE_FORMSETS
        ]

    steps = _admissionvariant_steps(variant)

    return render_backoffice(
        request,
        'backoffice/content/admission/variant_edit.html',
        active='admission',
        page_title=f'{variant.department.name} · {variant.grade.name} — {variant.page.region.name}',
        context={
            'variant': variant,
            'page': variant.page,
            'form': form,
            'formsets': formsets,
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(steps),
            'translatable_bases_json': json.dumps(list(ADMISSION_VARIANT_TRANSLATABLE)),
            'variant_translate_url': reverse('backoffice:content_admission_variant_translate', kwargs={'vpk': variant.pk}),
        },
    )


@require_POST
@backoffice_required
def content_admission_variant_translate(request, vpk):
    _get_admission_variant_for_user(request, vpk)
    return run_translate(request)


@require_POST
@backoffice_required
def content_admission_variant_seo(request, vpk):
    _get_admission_variant_for_user(request, vpk)
    return run_seo(request, empty_hint='Заполни h1/hero_lead на RU.')
