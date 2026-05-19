"""ProgramPage edit + AI-translate/SEO. Шаблон рендерит 6 inline-formset'ов
из конфигурации `PROGRAM_INLINE_FORMSETS` — единое место правды."""

import json

from django.contrib import messages
from django.db.models import Count, Max
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from programs.models import ProgramPage

from ...forms import (
    PROGRAM_FIXED_SLOT_COUNT,
    PROGRAM_FIXED_SLOT_SECTIONS,
    PROGRAM_INLINE_FORMSETS,
    PROGRAM_TRANSLATABLE,
    ProgramPageEditForm,
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


@never_cache
@backoffice_required
def content_program_list(request):
    qs = (
        region_scoped(ProgramPage.objects.select_related('region'), request.user)
        .annotate(
            audience_count=Count('audience_items', distinct=True),
            variant_count=Count('variant_cards', distinct=True),
            faq_count=Count('faq_items', distinct=True),
        )
        .order_by('region__name')
    )
    return render_backoffice(
        request,
        'backoffice/content/program/list.html',
        active='programs',
        page_title='Программа',
        context={'rows': qs},
    )


def _get_program_for_user(request, pk):
    return get_for_user_or_404(ProgramPage.objects.all(), request, pk)


def _programpage_steps(program):
    """Шаги stepper'а completeness на edit-странице.

    Ключевой набор полей (не каждый — иначе 35+ полей в чек-листе шумят).
    Inline-секция — read-only счётчик (JS не отслеживает изменения formset'ов).
    """
    ru_fields = [
        'hero_badge_text_ru', 'hero_title_ru', 'hero_subtitle_ru',
        'hero_cta_primary_text_ru', 'hero_cta_secondary_text_ru',
        'audience_label_ru', 'audience_title_ru',
        'benefits_label_ru', 'benefits_title_ru',
        'programs_label_ru', 'programs_title_ru',
        'team_label_ru', 'team_title_ru',
        'certificate_label_ru', 'certificate_title_ru',
        'activities_label_ru', 'activities_title_ru',
        'stats_label_ru', 'stats_title_ru',
        'faq_label_ru', 'faq_title_ru',
    ]
    kk_fields = [f.replace('_ru', '_kk') for f in ru_fields]
    en_fields = [f.replace('_ru', '_en') for f in ru_fields]
    seo_fields = ['seo_title_ru', 'seo_description_ru', 'og_title_ru', 'og_description_ru']

    inline_total = sum(
        getattr(program, related_name).count()
        for _prefix, _cls, related_name, _label, _bases in PROGRAM_INLINE_FORMSETS
    )

    return [
        make_step(program, id='ru', label='Основа (RU)', fields=ru_fields, required=True),
        make_step(program, id='kk', label='Перевод KZ', fields=kk_fields),
        make_step(program, id='en', label='Перевод EN', fields=en_fields),
        make_step(program, id='seo', label='SEO', fields=seo_fields),
        make_readonly_step(id='inline', label='Карточки', filled=inline_total, total=inline_total),
    ]


def _ensure_program_fixed_sections(program):
    """Гарантирует, что у программы есть ровно `PROGRAM_FIXED_SLOT_COUNT`
    (=4) строк в каждой «фиксированной» секции.

    Если строк меньше — создаёт пустые placeholder'ы (модельная валидация на
    .create() не срабатывает; форма уже отмечает поля как `required=False`).
    Если строк больше — оставляет (max_num=4 в формсете блокирует добавление
    через UI).
    """
    for related_name, model in PROGRAM_FIXED_SLOT_SECTIONS:
        qs = getattr(program, related_name)
        existing = qs.count()
        if existing >= PROGRAM_FIXED_SLOT_COUNT:
            continue
        max_order = qs.aggregate(_m=Max('order'))['_m'] or 0
        for i in range(PROGRAM_FIXED_SLOT_COUNT - existing):
            model.objects.create(
                program_page=program,
                order=max_order + (i + 1) * 10,
            )


@never_cache
@backoffice_required
def content_program_edit(request, pk):
    program = _get_program_for_user(request, pk)

    # Гарантируем 4 слота в фиксированных секциях ДО инициализации formset'ов.
    _ensure_program_fixed_sections(program)

    if request.method == 'POST':
        form = ProgramPageEditForm(request.POST, request.FILES, instance=program)
        formsets = [
            (prefix, fs_cls(request.POST, request.FILES, instance=program, prefix=prefix), related_name, label, bases)
            for prefix, fs_cls, related_name, label, bases in PROGRAM_INLINE_FORMSETS
        ]
        all_valid = form.is_valid() and all(fs.is_valid() for _, fs, *_ in formsets)
        if all_valid:
            form.save()
            for _, fs, *_ in formsets:
                fs.save()
            messages.success(request, 'Лендинг «Программа» сохранён.')
            return redirect('backoffice:content_program_edit', pk=program.pk)
    else:
        form = ProgramPageEditForm(instance=program)
        formsets = [
            (prefix, fs_cls(instance=program, prefix=prefix), related_name, label, bases)
            for prefix, fs_cls, related_name, label, bases in PROGRAM_INLINE_FORMSETS
        ]

    steps = _programpage_steps(program)

    return render_backoffice(
        request,
        'backoffice/content/program/edit.html',
        active='programs',
        page_title=f'Программа — {program.region.name}',
        context={
            'program': program,
            'form': form,
            'formsets': formsets,
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(steps),
            'translatable_bases_json': json.dumps(list(PROGRAM_TRANSLATABLE)),
        },
    )


@require_POST
@backoffice_required
def content_program_translate(request, pk):
    _get_program_for_user(request, pk)
    return run_translate(request)


@require_POST
@backoffice_required
def content_program_seo(request, pk):
    _get_program_for_user(request, pk)
    return run_seo(request, empty_hint='Заполни hero_title/hero_subtitle на RU.')
