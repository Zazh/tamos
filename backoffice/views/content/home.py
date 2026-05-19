"""HomePage edit + AJAX-галерея + AI-translate/SEO."""

import json

from django.contrib import messages
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from pages.models import HomeGalleryImage, HomePage

from ...forms import HOME_TRANSLATABLE, HomePageEditForm, TRANSLATION_LANGS
from ...shortcuts import backoffice_required, region_scoped, render_backoffice
from .._common import (
    get_for_user_or_404,
    make_step,
    run_seo,
    run_translate,
)


@never_cache
@backoffice_required
def content_home_list(request):
    qs = (
        region_scoped(HomePage.objects.select_related('region'), request.user)
        .annotate(gallery_count=Count('gallery'))
        .order_by('region__name')
    )
    return render_backoffice(
        request,
        'backoffice/content/home/list.html',
        active='home',
        page_title='Главная',
        context={'rows': qs},
    )


def _serialize_gallery_item(img):
    """JSON-представление одной картинки HomeGallery. Своя сериализация (а не
    общая `serialize_gallery_image`), потому что у HomeGalleryImage есть
    `orientation` — портретный/landscape (для strict-zip раскладки).
    """
    return {
        'pk': img.pk,
        'url': img.image.url if img.image else '',
        'orientation': img.orientation,
        'order': img.order,
        'alt_text_ru': img.alt_text_ru or '',
        'alt_text_kk': img.alt_text_kk or '',
        'alt_text_en': img.alt_text_en or '',
    }


def _human_size(num_bytes):
    """`1234567` → `'1.2 MB'`. Локальный — нужен только видеофайлу на edit-странице."""
    if num_bytes is None:
        return ''
    for unit in ('B', 'KB', 'MB', 'GB'):
        if num_bytes < 1024:
            return f'{num_bytes:.1f} {unit}' if unit != 'B' else f'{num_bytes} B'
        num_bytes /= 1024
    return f'{num_bytes:.1f} TB'


def _homepage_steps(home):
    """Шаги stepper'а completeness на edit-странице HomePage.

    Каждый шаг — dict с `fields` (имена form-инпутов), `filled` (сколько
    заполнено на сервере). Frontend (`boFormSteps` Alpine) пересчитывает
    `filled` на лету по input-событиям. Если у шага `required=True` и
    `filled < total` — кнопка Save disabled.
    """
    ru_fields = [
        'hero_image',
        'hero_badge_text_ru',
        'hero_title_ru',
        'hero_subtitle_ru',
        'hero_cta_primary_text_ru',
        'hero_cta_secondary_text_ru',
        'about_label_ru',
        'about_title_ru',
        'about_body_ru',
    ]
    kk_fields = [
        'hero_badge_text_kk', 'hero_title_kk', 'hero_subtitle_kk',
        'hero_cta_primary_text_kk', 'hero_cta_secondary_text_kk',
        'about_label_kk', 'about_title_kk', 'about_body_kk',
    ]
    en_fields = [
        'hero_badge_text_en', 'hero_title_en', 'hero_subtitle_en',
        'hero_cta_primary_text_en', 'hero_cta_secondary_text_en',
        'about_label_en', 'about_title_en', 'about_body_en',
    ]
    seo_fields = [
        'seo_title_ru', 'seo_description_ru', 'og_title_ru', 'og_description_ru',
    ]
    video_fields = ['video_file']

    return [
        make_step(home, id='ru', label='Основа (RU)', fields=ru_fields, required=True),
        make_step(home, id='kk', label='Перевод KZ', fields=kk_fields),
        make_step(home, id='en', label='Перевод EN', fields=en_fields),
        make_step(home, id='seo', label='SEO', fields=seo_fields),
        make_step(home, id='video', label='Шоурил', fields=video_fields),
    ]


@never_cache
@backoffice_required
def content_home_edit(request, pk):
    home = get_for_user_or_404(HomePage.objects.select_related('region'), request, pk)

    if request.method == 'POST':
        form = HomePageEditForm(request.POST, request.FILES, instance=home)
        if form.is_valid():
            form.save()
            messages.success(request, 'Главная страница сохранена.')
            return redirect('backoffice:content_home_edit', pk=home.pk)
    else:
        form = HomePageEditForm(instance=home)

    gallery_items = [_serialize_gallery_item(img) for img in home.gallery.all()]

    video_size_human = ''
    if home.video_file:
        try:
            video_size_human = _human_size(home.video_file.size)
        except (OSError, ValueError):
            video_size_human = '—'

    steps = _homepage_steps(home)

    return render_backoffice(
        request,
        'backoffice/content/home/edit.html',
        active='home',
        page_title=f'Главная — {home.region.name}',
        context={
            'home': home,
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
            'gallery_items_json': json.dumps(gallery_items),
            'video_size_human': video_size_human,
            'steps_json': json.dumps(steps),
            'translatable_bases_json': json.dumps(list(HOME_TRANSLATABLE)),
            'home_translate_url': reverse('backoffice:content_home_translate', kwargs={'pk': home.pk}),
        },
    )


def _get_home_for_user(request, pk):
    return get_for_user_or_404(HomePage.objects.all(), request, pk)


@require_POST
@backoffice_required
def content_home_gallery_upload(request, pk):
    """Multi-upload новых картинок. `orientation` определяется в save() модели,
    после — весь список (старые+новые) расставляется strict-zip-ом, order
    пересохраняется с шагом 10."""
    home = _get_home_for_user(request, pk)
    files = request.FILES.getlist('images')
    if not files:
        return JsonResponse({'error': 'No files'}, status=400)

    for f in files:
        HomeGalleryImage.objects.create(home_page=home, image=f, order=9999)

    # Strict-zip reorder всего списка
    arranged = HomeGalleryImage.strict_zip_arrange(home.gallery.all())
    for i, img in enumerate(arranged):
        new_order = i * 10
        if img.order != new_order:
            img.order = new_order
            img.save(update_fields=['order'])

    items = [_serialize_gallery_item(img) for img in home.gallery.all()]
    return JsonResponse({'items': items})


@require_POST
@backoffice_required
def content_home_gallery_reorder(request, pk):
    """Сохранить порядок, заданный менеджером через DnD. Не пересортируем —
    уважаем выбор пользователя (он мог намеренно сломать strict-zip)."""
    home = _get_home_for_user(request, pk)
    try:
        payload = json.loads(request.body or '{}')
        order = list(payload.get('order') or [])
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    own_ids = set(home.gallery.values_list('pk', flat=True))
    safe_order = [int(pk_) for pk_ in order if int(pk_) in own_ids]

    for i, pk_ in enumerate(safe_order):
        HomeGalleryImage.objects.filter(pk=pk_).update(order=i * 10)
    return JsonResponse({'ok': True})


@require_POST
@backoffice_required
def content_home_gallery_update(request, pk, gpk):
    """Inline-update alt_text translations."""
    home = _get_home_for_user(request, pk)
    img = get_object_or_404(HomeGalleryImage, pk=gpk, home_page=home)
    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    for field in ('alt_text_ru', 'alt_text_kk', 'alt_text_en'):
        if field in payload:
            setattr(img, field, str(payload[field])[:200])
    # base — копия ru (modeltranslation требует не-пустую base для fallback)
    img.alt_text = img.alt_text_ru or img.alt_text or ''
    img.save(update_fields=['alt_text', 'alt_text_ru', 'alt_text_kk', 'alt_text_en'])
    return JsonResponse({'ok': True, 'item': _serialize_gallery_item(img)})


@require_POST
@backoffice_required
def content_home_gallery_delete(request, pk, gpk):
    home = _get_home_for_user(request, pk)
    img = get_object_or_404(HomeGalleryImage, pk=gpk, home_page=home)
    img.delete()
    return JsonResponse({'ok': True})


@require_POST
@backoffice_required
def content_home_translate(request, pk):
    _get_home_for_user(request, pk)  # 404 если не в region-scope
    return run_translate(request)


@require_POST
@backoffice_required
def content_home_seo(request, pk):
    _get_home_for_user(request, pk)
    return run_seo(request, empty_hint='Заполни хотя бы hero_title/about_body на RU.')
