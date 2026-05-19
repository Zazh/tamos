"""Gallery (album-based): list / create / edit / delete альбомов + inline
grid фото внутри (bulk upload / toggle / update / delete / translate) + taxonomy
CRUD.

Архитектура копирует blog: Album = «пост», GalleryImage = фото внутри. На
публичной странице — плоская лента всех фото региона по `-created_at`, с
фильтром по `album.category`.
"""

import json

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from gallery.models import Album, GalleryCategory, GalleryImage
from regions.models import Region

from ...forms import AlbumEditForm, TRANSLATION_LANGS
from ...shortcuts import backoffice_required, region_scoped, render_backoffice
from .._common import (
    auto_slug,
    get_for_user_or_404,
    make_published_chips,
    run_translate,
)


ALBUMS_PER_PAGE = 24
GALLERY_WIDE_RATIO_THRESHOLD = 1.4  # ratio = width/height; >= → широкая


def _detect_is_wide(uploaded_file):
    """Авто-определение `is_wide` по aspect ratio. PIL открывает файл, потом
    делаем seek(0), чтобы Django сохранил его как обычно."""
    try:
        from PIL import Image
        uploaded_file.seek(0)
        with Image.open(uploaded_file) as im:
            w, h = im.size
        uploaded_file.seek(0)
        if not h:
            return False
        return (w / h) >= GALLERY_WIDE_RATIO_THRESHOLD
    except Exception:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        return False


def _serialize_gallery_image(img):
    thumb_url = ''
    if img.image:
        try:
            thumb_url = img.image_compressed.url
        except Exception:
            thumb_url = img.image.url
    return {
        'pk': img.pk,
        'thumb_url': thumb_url,
        'url': img.image.url if img.image else '',
        'alt_ru': img.alt_ru or '',
        'alt_kk': img.alt_kk or '',
        'alt_en': img.alt_en or '',
        'caption_ru': img.caption_ru or '',
        'caption_kk': img.caption_kk or '',
        'caption_en': img.caption_en or '',
        'is_wide': img.is_wide,
        'is_published': img.is_published,
    }


def _auto_slug_for_album(title):
    return auto_slug(title, model=Album, prefix='album')


def _get_album_for_user(request, pk):
    return get_for_user_or_404(
        Album.objects.select_related('region', 'category'),
        request,
        pk,
        region_field='region',
    )


@never_cache
@backoffice_required
def content_gallery_list(request):
    """Список альбомов. Region-scoped + chip-фильтр статуса + фильтр категории +
    region для su + поиск."""
    base_qs = region_scoped(
        Album.objects.select_related('region', 'category'),
        request.user,
    ).annotate(photo_count=Count('images'))

    category_slug = request.GET.get('category', '').strip()
    region_slug = request.GET.get('region', '').strip()
    q = request.GET.get('q', '').strip()

    pre_status_qs = base_qs
    if category_slug:
        pre_status_qs = pre_status_qs.filter(category__slug=category_slug)
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

    qs = qs.order_by('-created_at', '-pk')

    paginator = Paginator(qs, ALBUMS_PER_PAGE)
    page = paginator.get_page(request.GET.get('page'))

    qs_dict = request.GET.copy()
    qs_dict.pop('page', None)
    base_qs_str = qs_dict.urlencode()

    categories = list(
        GalleryCategory.objects.filter(is_published=True).order_by('order', 'name')
    )

    return render_backoffice(
        request,
        'backoffice/content/gallery/list.html',
        active='gallery',
        page_title='Фотогалерея',
        context={
            'page': page,
            'paginator': paginator,
            'categories': categories,
            'all_regions': Region.objects.filter(is_active=True) if request.user.is_superuser else None,
            'filters': {
                'status': is_published,
                'category': category_slug,
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
def content_gallery_create(request):
    """Создание альбома — минимум: title + category + region. Slug автогенерится."""
    if request.method == 'POST':
        form = AlbumEditForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            album = form.save(commit=False)
            title = form.cleaned_data.get('title_ru') or album.title or 'Без названия'
            album.slug = _auto_slug_for_album(title)
            album.is_published = bool(request.POST.get('publish_now'))
            album.save()
            form.save_m2m()
            if album.is_published:
                messages.success(request, f'Альбом «{album.title}» создан и опубликован.')
            else:
                messages.success(request, f'Черновик альбома «{album.title}» сохранён.')
            return redirect('backoffice:content_gallery_edit', pk=album.pk)
    else:
        form = AlbumEditForm(user=request.user)

    return render_backoffice(
        request,
        'backoffice/content/gallery/create.html',
        active='gallery',
        page_title='Новый альбом',
        context={
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
        },
    )


@never_cache
@backoffice_required
def content_gallery_edit(request, pk):
    """Edit альбома: метаданные + grid фото внутри (AJAX upload/toggle/delete)."""
    album = _get_album_for_user(request, pk)
    original_slug = album.slug
    original_region_id = album.region_id

    if request.method == 'POST':
        form = AlbumEditForm(request.POST, request.FILES, instance=album, user=request.user)
        if form.is_valid():
            saved = form.save(commit=False)
            saved.region_id = original_region_id
            if not saved.slug:
                saved.slug = original_slug
            saved.save()
            form.save_m2m()
            messages.success(request, 'Альбом сохранён.')
            return redirect('backoffice:content_gallery_edit', pk=saved.pk)
    else:
        form = AlbumEditForm(instance=album, user=request.user)

    photos_payload = [
        _serialize_gallery_image(img)
        for img in album.images.all().order_by('-created_at', '-pk')
    ]

    return render_backoffice(
        request,
        'backoffice/content/gallery/edit.html',
        active='gallery',
        page_title=f'Альбом · {album.title or "Без названия"}',
        context={
            'album': album,
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
            'photos_json': json.dumps(photos_payload),
            'photo_upload_url': reverse('backoffice:content_gallery_photo_upload', kwargs={'pk': album.pk}),
            'photo_toggle_url_tpl': reverse('backoffice:content_gallery_photo_toggle', kwargs={'pk': album.pk, 'ipk': 0}),
            'photo_update_url_tpl': reverse('backoffice:content_gallery_photo_update', kwargs={'pk': album.pk, 'ipk': 0}),
            'photo_delete_url_tpl': reverse('backoffice:content_gallery_photo_delete', kwargs={'pk': album.pk, 'ipk': 0}),
            'photo_translate_url_tpl': reverse('backoffice:content_gallery_photo_translate', kwargs={'pk': album.pk, 'ipk': 0}),
        },
    )


@require_POST
@backoffice_required
def content_gallery_delete(request, pk):
    album = _get_album_for_user(request, pk)
    title = album.title or f'Альбом #{album.pk}'
    photo_count = album.images.count()
    album.delete()  # CASCADE удалит и фото
    if photo_count:
        messages.success(request, f'Альбом «{title}» и {photo_count} фото удалены.')
    else:
        messages.success(request, f'Альбом «{title}» удалён.')
    return redirect('backoffice:content_gallery_list')


# ----- Photos внутри альбома (AJAX) -----------------------------------------


@require_POST
@backoffice_required
def content_gallery_photo_upload(request, pk):
    """Bulk upload фото в альбом. region/category берутся из альбома.
    Auto-detect is_wide по aspect ratio."""
    album = _get_album_for_user(request, pk)
    files = request.FILES.getlist('images')
    if not files:
        return JsonResponse({'error': 'No files'}, status=400)

    created = []
    for f in files:
        is_wide = _detect_is_wide(f)
        img = GalleryImage.objects.create(
            album=album,
            region=album.region,  # legacy mirror
            category=album.category,  # legacy mirror
            image=f,
            is_wide=is_wide,
            is_published=True,
        )
        created.append(_serialize_gallery_image(img))
    return JsonResponse({'items': created})


@require_POST
@backoffice_required
def content_gallery_photo_toggle(request, pk, ipk):
    album = _get_album_for_user(request, pk)
    img = get_object_or_404(GalleryImage, pk=ipk, album=album)
    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    field = str(payload.get('field') or '')
    if field not in ('is_wide', 'is_published'):
        return JsonResponse({'error': 'Invalid field'}, status=400)
    value = bool(payload.get('value'))
    setattr(img, field, value)
    img.save(update_fields=[field, 'updated_at'])
    return JsonResponse({'ok': True, 'item': _serialize_gallery_image(img)})


@require_POST
@backoffice_required
def content_gallery_photo_update(request, pk, ipk):
    album = _get_album_for_user(request, pk)
    img = get_object_or_404(GalleryImage, pk=ipk, album=album)
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
        'updated_at',
    ])
    return JsonResponse({'ok': True, 'item': _serialize_gallery_image(img)})


@require_POST
@backoffice_required
def content_gallery_photo_delete(request, pk, ipk):
    album = _get_album_for_user(request, pk)
    img = get_object_or_404(GalleryImage, pk=ipk, album=album)
    img.delete()
    return JsonResponse({'ok': True})


@require_POST
@backoffice_required
def content_gallery_photo_translate(request, pk, ipk):
    """RU→KK/EN перевод alt+caption одной фотографии."""
    album = _get_album_for_user(request, pk)
    get_object_or_404(GalleryImage, pk=ipk, album=album)
    return run_translate(request)


# ----- Taxonomy (категории — глобальные, как у blog) ------------------------


@never_cache
@backoffice_required
@require_http_methods(['GET', 'POST'])
def content_gallery_taxonomy(request):
    categories = list(
        GalleryCategory.objects
        .annotate(album_count=Count('albums'))
        .order_by('order', 'name')
    )

    return render_backoffice(
        request,
        'backoffice/content/gallery/taxonomy.html',
        active='gallery',
        page_title='Фотогалерея · темы (категории)',
        context={
            'categories': categories,
        },
    )


def _gallery_taxonomy_save(request):
    pk = request.POST.get('pk') or ''
    if pk:
        obj = get_object_or_404(GalleryCategory.objects.all(), pk=pk)
        for lang in TRANSLATION_LANGS:
            key = f'name_{lang}'
            if key in request.POST:
                setattr(obj, key, request.POST.get(key, '').strip()[:80])
        obj.name = obj.name_ru or obj.name or ''
        obj.is_published = bool(request.POST.get('is_published'))
        obj.save()
        messages.success(request, f'Тема «{obj.name}» обновлена.')
    else:
        name_ru = (request.POST.get('name_ru') or '').strip()
        if not name_ru:
            messages.error(request, 'Введите название темы.')
            return
        from django.utils.text import slugify
        from itertools import count
        base_slug = slugify(name_ru, allow_unicode=False) or 'category'
        slug = base_slug[:60]
        for i in count(1):
            if not GalleryCategory.objects.filter(slug=slug).exists():
                break
            slug = f'{base_slug[:55]}-{i}'
        max_order = GalleryCategory.objects.aggregate(Max('order'))['order__max'] or 0
        obj = GalleryCategory.objects.create(
            slug=slug,
            name=name_ru[:80],
            name_ru=name_ru[:80],
            order=max_order + 10,
        )
        messages.success(request, f'Тема «{obj.name}» создана.')


@require_POST
@backoffice_required
def content_gallery_category_save(request):
    _gallery_taxonomy_save(request)
    return redirect('backoffice:content_gallery_taxonomy')


@require_POST
@backoffice_required
def content_gallery_category_delete(request, pk):
    cat = get_object_or_404(GalleryCategory.objects.all(), pk=pk)
    name = cat.name
    album_count = cat.albums.count()
    if album_count:
        messages.error(
            request,
            f'Нельзя удалить тему «{name}» — к ней привязано {album_count} альбомов. '
            'Перенесите их в другую тему сначала.',
        )
    else:
        cat.delete()
        messages.success(request, f'Тема «{name}» удалена.')
    return redirect('backoffice:content_gallery_taxonomy')
