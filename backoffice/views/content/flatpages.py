"""Flat pages: статичные региональные страницы (About / Uniform / Privacy).

Без даты публикации (только is_published), без таксономии. Slug —
семантический, на edit неизменяем; линкуется в NavItem.flat_page через FK.
Главная inline-галерея (slug='main') рендерится после контента — по
образцу blog/events.
"""

import json

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from core.image_optimize import normalize_uploaded_image
from pages.models import FlatPage, FlatPageGallery, FlatPageGalleryImage
from regions.models import Region

from ...forms import (
    FLATPAGE_OUT_OF_FORM_BASES,
    FLATPAGE_TRANSLATABLE,
    FlatPageEditForm,
    TRANSLATION_LANGS,
)
from ...shortcuts import backoffice_required, region_scoped, render_backoffice
from .._common import (
    get_for_user_or_404,
    make_blank_step,
    make_published_chips,
    make_step,
    run_seo,
    run_translate,
)


FLATPAGES_PER_PAGE = 30
FLATPAGE_MAIN_GALLERY_SLUG = 'main'


def _get_flatpage_for_user(request, pk):
    return get_for_user_or_404(FlatPage.objects.select_related('region'), request, pk)


def _get_or_create_flatpage_main_gallery(page):
    gallery, _ = FlatPageGallery.objects.get_or_create(
        flat_page=page,
        slug=FLATPAGE_MAIN_GALLERY_SLUG,
        defaults={'title': 'Главная галерея', 'order': 0},
    )
    return gallery


def _serialize_flatpage_gallery_image(img):
    return {
        'pk': img.pk,
        'url': img.image.url if img.image else '',
        'alt_ru': img.alt_ru or '',
        'alt_kk': img.alt_kk or '',
        'alt_en': img.alt_en or '',
        'caption_ru': img.caption_ru or '',
        'caption_kk': img.caption_kk or '',
        'caption_en': img.caption_en or '',
        'order': img.order,
    }


def _flatpage_steps(page):
    ru_fields = ['title_ru', 'content_ru']
    kk_fields = ['title_kk', 'content_kk']
    en_fields = ['title_en', 'content_en']
    seo_fields = ['seo_title_ru', 'seo_description_ru', 'og_title_ru', 'og_image']

    return [
        make_step(page, id='ru', label='Основа (RU)', fields=ru_fields, required=True),
        make_step(page, id='kk', label='Перевод KZ', fields=kk_fields),
        make_step(page, id='en', label='Перевод EN', fields=en_fields),
        make_step(page, id='seo', label='SEO', fields=seo_fields),
    ]


def _flatpage_steps_for_create():
    return [
        make_blank_step(id='ru', label='Основа (RU)', total=2, required=True),
        make_blank_step(id='kk', label='Перевод KZ', total=2),
        make_blank_step(id='en', label='Перевод EN', total=2),
        make_blank_step(id='seo', label='SEO', total=4),
    ]


@never_cache
@backoffice_required
def content_flatpages_list(request):
    base_qs = region_scoped(FlatPage.objects.select_related('region'), request.user)

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

    is_published = request.GET.get('status', '').strip()
    qs = pre_status_qs
    if is_published == 'published':
        qs = qs.filter(is_published=True)
    elif is_published == 'draft':
        qs = qs.filter(is_published=False)

    qs = qs.order_by('region__name', 'slug')

    paginator = Paginator(qs, FLATPAGES_PER_PAGE)
    page = paginator.get_page(request.GET.get('page'))

    qs_dict = request.GET.copy()
    qs_dict.pop('page', None)
    base_qs_str = qs_dict.urlencode()

    return render_backoffice(
        request,
        'backoffice/content/flatpages/list.html',
        active='flatpages',
        page_title='Доп. страницы',
        context={
            'page': page,
            'paginator': paginator,
            'all_regions': Region.objects.filter(is_active=True) if request.user.is_superuser else None,
            'filters': {
                'status': is_published,
                'region': region_slug,
                'q': q,
            },
            'status_chips': make_published_chips(request, counts=status_counts, active=is_published),
            'base_qs': base_qs_str,
        },
    )


@never_cache
@backoffice_required
@require_http_methods(['GET', 'POST'])
def content_flatpages_create(request):
    if request.method == 'POST':
        form = FlatPageEditForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            page = form.save(commit=False)
            page.is_published = bool(request.POST.get('publish_now'))
            try:
                page.save()
            except Exception:
                # IntegrityError при дубликате (region, slug). Дружественная подсказка.
                form.add_error(
                    'slug',
                    f'Страница со slug «{page.slug}» уже есть в этом регионе. '
                    'Выбери другой slug или редактируй существующую.',
                )
            else:
                form.save_m2m()
                if page.is_published:
                    messages.success(request, f'Страница «{page.title}» опубликована.')
                else:
                    messages.success(request, f'Черновик «{page.title}» сохранён.')
                return redirect('backoffice:content_flatpages_edit', pk=page.pk)
    else:
        form = FlatPageEditForm(user=request.user)

    steps = _flatpage_steps_for_create()

    return render_backoffice(
        request,
        'backoffice/content/flatpages/create.html',
        active='flatpages',
        page_title='Новая доп. страница',
        context={
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(steps),
            'translatable_bases_json': json.dumps(list(FLATPAGE_TRANSLATABLE)),
            'out_of_form_bases': FLATPAGE_OUT_OF_FORM_BASES,
        },
    )


@never_cache
@backoffice_required
def content_flatpages_edit(request, pk):
    page = _get_flatpage_for_user(request, pk)
    # ModelForm мутирует instance — сохраняем оригиналы slug/region_id ДО init.
    original_slug = page.slug
    original_region_id = page.region_id

    if request.method == 'POST':
        form = FlatPageEditForm(request.POST, request.FILES, instance=page, user=request.user)
        if form.is_valid():
            saved = form.save(commit=False)
            saved.region_id = original_region_id
            if not saved.slug:
                saved.slug = original_slug
            saved.save()
            form.save_m2m()
            messages.success(request, 'Страница сохранена.')
            return redirect('backoffice:content_flatpages_edit', pk=saved.pk)
    else:
        form = FlatPageEditForm(instance=page, user=request.user)

    steps = _flatpage_steps(page)

    gallery_items = []
    main_gallery = FlatPageGallery.objects.filter(flat_page=page, slug=FLATPAGE_MAIN_GALLERY_SLUG).first()
    if main_gallery:
        gallery_items = [
            _serialize_flatpage_gallery_image(i)
            for i in main_gallery.images.all().order_by('order', 'pk')
        ]

    return render_backoffice(
        request,
        'backoffice/content/flatpages/edit.html',
        active='flatpages',
        page_title=f'Доп. страница · {page.title or "Без названия"}',
        context={
            'page_obj': page,
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(steps),
            'translatable_bases_json': json.dumps(list(FLATPAGE_TRANSLATABLE)),
            'out_of_form_bases': FLATPAGE_OUT_OF_FORM_BASES,
            'flatpages_translate_url': reverse('backoffice:content_flatpages_translate', kwargs={'pk': page.pk}),
            'flatpages_seo_url': reverse('backoffice:content_flatpages_seo', kwargs={'pk': page.pk}),
            'gallery_items_json': json.dumps(gallery_items),
            'gallery_upload_url': reverse('backoffice:content_flatpages_gallery_upload', kwargs={'pk': page.pk}),
            'gallery_reorder_url': reverse('backoffice:content_flatpages_gallery_reorder', kwargs={'pk': page.pk}),
            'gallery_update_url_tpl': reverse('backoffice:content_flatpages_gallery_update', kwargs={'pk': page.pk, 'gpk': 0}),
            'gallery_delete_url_tpl': reverse('backoffice:content_flatpages_gallery_delete', kwargs={'pk': page.pk, 'gpk': 0}),
        },
    )


@require_POST
@backoffice_required
def content_flatpages_delete(request, pk):
    page = _get_flatpage_for_user(request, pk)
    title = page.title or f'Страница #{page.pk}'
    # Если на эту FlatPage ссылается NavItem.flat_page — предупреждаем, не запрещаем.
    from navigation.models import NavItem
    linked = NavItem.objects.filter(flat_page=page).count()
    page.delete()
    if linked:
        messages.success(
            request,
            f'Страница «{title}» удалена. Учти: с ней была связана {linked} ссылка в меню — проверь навигацию.',
        )
    else:
        messages.success(request, f'Страница «{title}» удалена.')
    return redirect('backoffice:content_flatpages_list')


@require_POST
@backoffice_required
def content_flatpages_seo(request, pk):
    _get_flatpage_for_user(request, pk)
    return run_seo(request, empty_hint='Заполни title и lead на RU.')


@require_POST
@backoffice_required
def content_flatpages_translate(request, pk):
    _get_flatpage_for_user(request, pk)
    return run_translate(request)


@require_POST
@backoffice_required
def content_flatpages_gallery_upload(request, pk):
    page = _get_flatpage_for_user(request, pk)
    files = request.FILES.getlist('images')
    if not files:
        return JsonResponse({'error': 'No files'}, status=400)

    gallery = _get_or_create_flatpage_main_gallery(page)
    max_order = gallery.images.aggregate(Max('order'))['order__max'] or 0
    for f in files:
        max_order += 10
        FlatPageGalleryImage.objects.create(
            gallery=gallery, image=normalize_uploaded_image(f), order=max_order,
        )

    items = [_serialize_flatpage_gallery_image(i) for i in gallery.images.all().order_by('order', 'pk')]
    return JsonResponse({'items': items})


@require_POST
@backoffice_required
def content_flatpages_gallery_reorder(request, pk):
    page = _get_flatpage_for_user(request, pk)
    try:
        payload = json.loads(request.body or '{}')
        order = list(payload.get('order') or [])
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    gallery = _get_or_create_flatpage_main_gallery(page)
    own_ids = set(gallery.images.values_list('pk', flat=True))
    safe_order = [int(p) for p in order if int(p) in own_ids]
    for i, p in enumerate(safe_order):
        FlatPageGalleryImage.objects.filter(pk=p).update(order=i * 10)
    return JsonResponse({'ok': True})


@require_POST
@backoffice_required
def content_flatpages_gallery_update(request, pk, gpk):
    page = _get_flatpage_for_user(request, pk)
    img = get_object_or_404(FlatPageGalleryImage, pk=gpk, gallery__flat_page=page)
    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    for field in ('alt_ru', 'alt_kk', 'alt_en', 'caption_ru', 'caption_kk', 'caption_en'):
        if field in payload:
            setattr(img, field, str(payload[field])[:300])
    img.alt = img.alt_ru or img.alt or ''
    img.caption = img.caption_ru or img.caption or ''
    img.save(update_fields=[
        'alt', 'alt_ru', 'alt_kk', 'alt_en',
        'caption', 'caption_ru', 'caption_kk', 'caption_en',
    ])
    return JsonResponse({'ok': True, 'item': _serialize_flatpage_gallery_image(img)})


@require_POST
@backoffice_required
def content_flatpages_gallery_delete(request, pk, gpk):
    page = _get_flatpage_for_user(request, pk)
    img = get_object_or_404(FlatPageGalleryImage, pk=gpk, gallery__flat_page=page)
    img.delete()
    return JsonResponse({'ok': True})
