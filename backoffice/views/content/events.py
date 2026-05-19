"""Events: список/create/edit/delete + inline-галерея + AI translate/SEO.

Клон blog минус taxonomy/author/tags.
"""

import json

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from events.models import Event, EventGallery, EventGalleryImage
from regions.models import Region

from ...forms import (
    EVENT_OUT_OF_FORM_BASES,
    EVENT_TRANSLATABLE,
    EventEditForm,
    TRANSLATION_LANGS,
)
from ...shortcuts import backoffice_required, region_scoped, render_backoffice
from .._common import (
    auto_slug,
    get_for_user_or_404,
    make_blank_step,
    make_published_chips,
    make_step,
    run_seo,
    run_translate,
)


EVENTS_PER_PAGE = 20
EVENT_MAIN_GALLERY_SLUG = 'main'


def _auto_slug_for_event(title):
    return auto_slug(title, model=Event, prefix='event')


def _get_event_for_user(request, pk):
    return get_for_user_or_404(Event.objects.select_related('region'), request, pk)


def _event_steps(event):
    ru_fields = ['title_ru', 'lead_ru', 'cover_image', 'content_ru']
    kk_fields = ['title_kk', 'lead_kk', 'content_kk']
    en_fields = ['title_en', 'lead_en', 'content_en']
    seo_fields = ['seo_title_ru', 'seo_description_ru', 'og_title_ru', 'og_image']
    pub_fields = ['is_published', 'published_at']

    return [
        make_step(event, id='ru', label='Основа (RU)', fields=ru_fields, required=True),
        make_step(event, id='kk', label='Перевод KZ', fields=kk_fields),
        make_step(event, id='en', label='Перевод EN', fields=en_fields),
        make_step(event, id='seo', label='SEO', fields=seo_fields),
        make_step(event, id='publish', label='Публикация', fields=pub_fields),
    ]


def _event_steps_for_create():
    return [
        make_blank_step(id='ru', label='Основа (RU)', total=4, required=True),
        make_blank_step(id='kk', label='Перевод KZ', total=3),
        make_blank_step(id='en', label='Перевод EN', total=3),
        make_blank_step(id='seo', label='SEO', total=4),
        make_blank_step(id='publish', label='Публикация', total=2),
    ]


@never_cache
@backoffice_required
def content_events_list(request):
    base_qs = region_scoped(Event.objects.select_related('region'), request.user)

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

    qs = qs.order_by('-published_at', '-pk')

    paginator = Paginator(qs, EVENTS_PER_PAGE)
    page = paginator.get_page(request.GET.get('page'))

    qs_dict = request.GET.copy()
    qs_dict.pop('page', None)
    base_qs_str = qs_dict.urlencode()

    return render_backoffice(
        request,
        'backoffice/content/events/list.html',
        active='events',
        page_title='События',
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
def content_events_create(request):
    if request.method == 'POST':
        post_data = request.POST.copy()
        if not post_data.get('published_at'):
            post_data['published_at'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
        form = EventEditForm(post_data, request.FILES, user=request.user)
        if form.is_valid():
            event = form.save(commit=False)
            title = form.cleaned_data.get('title_ru') or event.title or 'Без названия'
            event.slug = _auto_slug_for_event(title)
            event.is_published = bool(request.POST.get('publish_now'))
            if not event.published_at:
                event.published_at = timezone.now()
            event.save()
            form.save_m2m()

            if event.is_published:
                messages.success(request, f'Событие «{event.title}» опубликовано.')
            else:
                messages.success(request, f'Черновик «{event.title}» сохранён.')
            return redirect('backoffice:content_events_edit', pk=event.pk)
    else:
        form = EventEditForm(
            initial={'published_at': timezone.now().strftime('%Y-%m-%dT%H:%M')},
            user=request.user,
        )

    steps = _event_steps_for_create()

    return render_backoffice(
        request,
        'backoffice/content/events/create.html',
        active='events',
        page_title='Новое событие',
        context={
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(steps),
            'translatable_bases_json': json.dumps(list(EVENT_TRANSLATABLE)),
            'out_of_form_bases': EVENT_OUT_OF_FORM_BASES,
        },
    )


@never_cache
@backoffice_required
def content_events_edit(request, pk):
    event = _get_event_for_user(request, pk)
    # ModelForm мутирует instance — сохраняем оригиналы slug/region_id ДО init.
    # См. [[feedback_modelform_mutates_instance]].
    original_slug = event.slug
    original_region_id = event.region_id

    if request.method == 'POST':
        form = EventEditForm(request.POST, request.FILES, instance=event, user=request.user)
        if form.is_valid():
            saved = form.save(commit=False)
            saved.region_id = original_region_id
            if not saved.slug:
                saved.slug = original_slug
            saved.save()
            form.save_m2m()
            messages.success(request, 'Событие сохранено.')
            return redirect('backoffice:content_events_edit', pk=saved.pk)
    else:
        form = EventEditForm(instance=event, user=request.user)

    steps = _event_steps(event)

    gallery_items = []
    main_gallery = EventGallery.objects.filter(event=event, slug=EVENT_MAIN_GALLERY_SLUG).first()
    if main_gallery:
        gallery_items = [
            _serialize_event_gallery_image(i)
            for i in main_gallery.images.all().order_by('order', 'pk')
        ]

    return render_backoffice(
        request,
        'backoffice/content/events/edit.html',
        active='events',
        page_title=f'События · {event.title or "Без названия"}',
        context={
            'event': event,
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(steps),
            'translatable_bases_json': json.dumps(list(EVENT_TRANSLATABLE)),
            'out_of_form_bases': EVENT_OUT_OF_FORM_BASES,
            'events_translate_url': reverse('backoffice:content_events_translate', kwargs={'pk': event.pk}),
            'events_seo_url': reverse('backoffice:content_events_seo', kwargs={'pk': event.pk}),
            'gallery_items_json': json.dumps(gallery_items),
            'gallery_upload_url': reverse('backoffice:content_events_gallery_upload', kwargs={'pk': event.pk}),
            'gallery_reorder_url': reverse('backoffice:content_events_gallery_reorder', kwargs={'pk': event.pk}),
            'gallery_update_url_tpl': reverse('backoffice:content_events_gallery_update', kwargs={'pk': event.pk, 'gpk': 0}),
            'gallery_delete_url_tpl': reverse('backoffice:content_events_gallery_delete', kwargs={'pk': event.pk, 'gpk': 0}),
        },
    )


def _get_or_create_event_main_gallery(event):
    gallery, _ = EventGallery.objects.get_or_create(
        event=event,
        slug=EVENT_MAIN_GALLERY_SLUG,
        defaults={'title': 'Главная галерея', 'order': 0},
    )
    return gallery


def _serialize_event_gallery_image(img):
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


@require_POST
@backoffice_required
def content_events_gallery_upload(request, pk):
    event = _get_event_for_user(request, pk)
    files = request.FILES.getlist('images')
    if not files:
        return JsonResponse({'error': 'No files'}, status=400)

    gallery = _get_or_create_event_main_gallery(event)
    max_order = gallery.images.aggregate(Max('order'))['order__max'] or 0
    for f in files:
        max_order += 10
        EventGalleryImage.objects.create(gallery=gallery, image=f, order=max_order)

    items = [_serialize_event_gallery_image(i) for i in gallery.images.all().order_by('order', 'pk')]
    return JsonResponse({'items': items})


@require_POST
@backoffice_required
def content_events_gallery_reorder(request, pk):
    event = _get_event_for_user(request, pk)
    try:
        payload = json.loads(request.body or '{}')
        order = list(payload.get('order') or [])
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    gallery = _get_or_create_event_main_gallery(event)
    own_ids = set(gallery.images.values_list('pk', flat=True))
    safe_order = [int(p) for p in order if int(p) in own_ids]
    for i, p in enumerate(safe_order):
        EventGalleryImage.objects.filter(pk=p).update(order=i * 10)
    return JsonResponse({'ok': True})


@require_POST
@backoffice_required
def content_events_gallery_update(request, pk, gpk):
    event = _get_event_for_user(request, pk)
    img = get_object_or_404(EventGalleryImage, pk=gpk, gallery__event=event)
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
    return JsonResponse({'ok': True, 'item': _serialize_event_gallery_image(img)})


@require_POST
@backoffice_required
def content_events_gallery_delete(request, pk, gpk):
    event = _get_event_for_user(request, pk)
    img = get_object_or_404(EventGalleryImage, pk=gpk, gallery__event=event)
    img.delete()
    return JsonResponse({'ok': True})


@require_POST
@backoffice_required
def content_events_delete(request, pk):
    event = _get_event_for_user(request, pk)
    title = event.title or f'Событие #{event.pk}'
    event.delete()
    messages.success(request, f'Событие «{title}» удалено.')
    return redirect('backoffice:content_events_list')


@require_POST
@backoffice_required
def content_events_seo(request, pk):
    _get_event_for_user(request, pk)
    return run_seo(request, empty_hint='Заполни title и lead на RU.')


@require_POST
@backoffice_required
def content_events_translate(request, pk):
    _get_event_for_user(request, pk)
    return run_translate(request)
