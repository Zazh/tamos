"""Blog: list/create/edit/delete + inline-галерея (main) + taxonomy + AI
translate/SEO/suggest_tags.

Шаблоны: `templates/backoffice/content/blog/`. Категории и теги — глобальные
(миграции 0006-0008).
"""

import json
import secrets

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from blog.models import BlogCategory, BlogGallery, BlogGalleryImage, BlogPost, BlogTag
from core.gemini_translate import (
    TranslationConfigError,
    TranslationError,
    suggest_tags,
)
from core.image_optimize import normalize_uploaded_image
from regions.models import Region

from ...forms import (
    BLOG_POST_OUT_OF_FORM_BASES,
    BLOG_POST_TRANSLATABLE,
    BlogPostEditForm,
    TRANSLATION_LANGS,
)
from ...shortcuts import backoffice_required, region_scoped, render_backoffice
from .._common import (
    auto_slug,
    get_for_user_or_404,
    make_published_chips,
    make_step,
    run_seo,
    run_translate,
)


BLOG_POSTS_PER_PAGE = 20
BLOG_MAIN_GALLERY_SLUG = 'main'
SUGGEST_TAGS_MAX_CONTENT = 10000
DRAFT_SLUG_PREFIX = 'draft-'


def _auto_slug_for_blog(title):
    return auto_slug(title, model=BlogPost, prefix='post')


def _new_draft_slug():
    # 4 байта = 8 hex-символов, 4 миллиарда вариантов; коллизия в БД ловится
    # UniqueConstraint(region, slug), но мы выбираем глобально-уникальный, чтобы
    # не зависеть от региона на момент создания черновика.
    for _ in range(5):
        slug = f'{DRAFT_SLUG_PREFIX}{secrets.token_hex(4)}'
        if not BlogPost.objects.filter(slug=slug).exists():
            return slug
    return f'{DRAFT_SLUG_PREFIX}{secrets.token_hex(8)}'


def _get_blog_post_for_user(request, pk):
    return get_for_user_or_404(
        BlogPost.objects.select_related('region', 'category').prefetch_related('tags'),
        request, pk,
    )


def _blogpost_steps(post):
    ru_fields = ['title_ru', 'lead_ru', 'cover_image', 'content_ru']
    kk_fields = ['title_kk', 'lead_kk', 'content_kk']
    en_fields = ['title_en', 'lead_en', 'content_en']
    seo_fields = ['seo_title_ru', 'seo_description_ru', 'og_title_ru']
    pub_fields = ['is_published', 'published_at']

    return [
        make_step(post, id='ru', label='Основа (RU)', fields=ru_fields, required=True),
        make_step(post, id='kk', label='Перевод KZ', fields=kk_fields),
        make_step(post, id='en', label='Перевод EN', fields=en_fields),
        make_step(post, id='seo', label='SEO', fields=seo_fields),
        make_step(post, id='publish', label='Публикация', fields=pub_fields),
    ]


def _sync_blog_post_tags(post, tags_data):
    """Привести M2M тегов поста к указанному списку.

    `tags_data` — `[{slug, name, names?}]`. Теги глобальные:
    - если тег найден по slug — добавляем в M2M;
    - если нет — создаём новый с name(_ru/kk/en если переданы) и order = max+10.

    Возвращает `(added_count, created_count)`.
    """
    desired_slugs = [t['slug'] for t in tags_data]
    if not desired_slugs:
        post.tags.clear()
        return (0, 0)

    existing = list(BlogTag.objects.filter(slug__in=desired_slugs))
    by_slug = {t.slug: t for t in existing}

    created = 0
    if len(by_slug) < len(desired_slugs):
        max_order = BlogTag.objects.aggregate(Max('order'))['order__max'] or 0
        for td in tags_data:
            slug = td['slug']
            if slug in by_slug:
                continue
            max_order += 10
            names = td.get('names') or {}
            tag = BlogTag.objects.create(
                slug=slug,
                name=td['name'],
                name_ru=names.get('ru') or td['name'],
                name_kk=names.get('kk') or '',
                name_en=names.get('en') or '',
                order=max_order,
            )
            by_slug[slug] = tag
            created += 1

    post.tags.set([by_slug[s] for s in desired_slugs if s in by_slug])
    return (len(desired_slugs), created)


def _tags_payload(qs):
    """Сериализатор тегов для `boTagPicker`. Возвращает имена на 3 языках —
    чипы реактивно меняются при смене таба RU/KK/EN."""
    return [
        {
            'slug': t.slug,
            'name': t.name,
            'names': {
                'ru': t.name_ru or t.name or '',
                'kk': t.name_kk or '',
                'en': t.name_en or '',
            },
        }
        for t in qs
    ]


@never_cache
@backoffice_required
def content_blog_list(request):
    base_qs = (
        region_scoped(BlogPost.objects.select_related('region', 'category'), request.user)
        .prefetch_related('tags')
    )

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

    qs = qs.order_by('-published_at', '-pk')

    paginator = Paginator(qs, BLOG_POSTS_PER_PAGE)
    page = paginator.get_page(request.GET.get('page'))

    qs_dict = request.GET.copy()
    qs_dict.pop('page', None)
    base_qs_str = qs_dict.urlencode()

    return render_backoffice(
        request,
        'backoffice/content/blog/list.html',
        active='blog',
        page_title='Блог',
        context={
            'page': page,
            'paginator': paginator,
            'categories': BlogCategory.objects.all().order_by('order', 'name'),
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


@require_POST
@backoffice_required
def content_blog_create(request):
    """Создаёт пустой draft и сразу редиректит на edit.

    Так галерея/теги/обложка доступны с первого экрана: всё в edit, без
    промежуточной create-формы. Менеджер заполняет инлайн, жмёт «Сохранить».
    Пустые draft'ы видны в списке как «Без названия» — можно удалить.

    `region`/`category` определяются автоматически: регион — из user (для su
    берётся первый активный), категория — первая в БД. Менеджер меняет на edit.
    """
    if request.user.is_superuser:
        region = Region.objects.filter(is_active=True).order_by('pk').first()
    else:
        region_id = getattr(request.user, 'manager_region_id', None)
        region = Region.objects.filter(pk=region_id).first() if region_id else None

    if region is None:
        messages.error(request, 'Не удалось определить регион. Создай регион или назначь его менеджеру.')
        return redirect('backoffice:content_blog_list')

    category = BlogCategory.objects.order_by('order', 'name').first()
    if category is None:
        messages.error(
            request,
            'Сначала создай хотя бы одну категорию в разделе «Категории и теги» — без неё пост не сохранить.',
        )
        return redirect('backoffice:content_blog_taxonomy')

    post = BlogPost.objects.create(
        region=region,
        category=category,
        slug=_new_draft_slug(),
        title='',
        content='',
        is_published=False,
        published_at=timezone.now(),
    )
    return redirect('backoffice:content_blog_edit', pk=post.pk)


@never_cache
@backoffice_required
def content_blog_edit(request, pk):
    post = _get_blog_post_for_user(request, pk)
    # ВАЖНО: ModelForm(data, instance=post) мутирует post под значения POST'а
    # (post и saved — один объект). Сохраняем оригиналы ДО init формы.
    # См. [[feedback_modelform_mutates_instance]].
    original_slug = post.slug
    original_region_id = post.region_id

    if request.method == 'POST':
        form = BlogPostEditForm(request.POST, request.FILES, instance=post, user=request.user)
        if form.is_valid():
            saved = form.save(commit=False)
            # Регион и slug на edit неизменяемы (hidden поля, могут прийти пустыми).
            saved.region_id = original_region_id
            if not saved.slug:
                saved.slug = original_slug
            # Первый save draft'а с заполненным title → пересчитать slug в
            # читаемый. Иначе URL поста останется `/blog/draft-abc12345/`.
            title_for_slug = (form.cleaned_data.get('title_ru') or saved.title or '').strip()
            if original_slug.startswith(DRAFT_SLUG_PREFIX) and title_for_slug:
                saved.slug = _auto_slug_for_blog(title_for_slug)
            saved.save()
            form.save_m2m()
            _sync_blog_post_tags(saved, form.cleaned_data.get('tags_json') or [])
            messages.success(request, 'Пост сохранён.')
            return redirect('backoffice:content_blog_edit', pk=saved.pk)
    else:
        form = BlogPostEditForm(instance=post, user=request.user)

    steps = _blogpost_steps(post)

    all_tags = _tags_payload(BlogTag.objects.all().order_by('order', 'name'))
    categories = list(BlogCategory.objects.all().order_by('order', 'name'))

    # Главная inline-галерея (slug='main'). Если её нет — items пустой, она
    # создастся лениво при первом upload.
    gallery_items = []
    main_gallery = BlogGallery.objects.filter(post=post, slug=BLOG_MAIN_GALLERY_SLUG).first()
    if main_gallery:
        gallery_items = [
            _serialize_blog_gallery_image(i)
            for i in main_gallery.images.all().order_by('order', 'pk')
        ]

    return render_backoffice(
        request,
        'backoffice/content/blog/edit.html',
        active='blog',
        page_title=f'Блог · {post.title or "Без названия"}',
        context={
            'post': post,
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
            'categories': categories,
            'all_tags_json': json.dumps(all_tags),
            'steps_json': json.dumps(steps),
            'translatable_bases_json': json.dumps(list(BLOG_POST_TRANSLATABLE)),
            'out_of_form_bases': BLOG_POST_OUT_OF_FORM_BASES,
            'blog_translate_url': reverse('backoffice:content_blog_translate', kwargs={'pk': post.pk}),
            'blog_seo_url': reverse('backoffice:content_blog_seo', kwargs={'pk': post.pk}),
            'blog_suggest_tags_url': reverse('backoffice:content_blog_suggest_tags', kwargs={'pk': post.pk}),
            'gallery_items_json': json.dumps(gallery_items),
            'gallery_upload_url': reverse('backoffice:content_blog_gallery_upload', kwargs={'pk': post.pk}),
            'gallery_reorder_url': reverse('backoffice:content_blog_gallery_reorder', kwargs={'pk': post.pk}),
            'gallery_update_url_tpl': reverse('backoffice:content_blog_gallery_update', kwargs={'pk': post.pk, 'gpk': 0}),
            'gallery_delete_url_tpl': reverse('backoffice:content_blog_gallery_delete', kwargs={'pk': post.pk, 'gpk': 0}),
        },
    )


# ----- Blog inline gallery (main gallery — one per post, auto-created) -------


def _get_or_create_main_gallery(post):
    gallery, _ = BlogGallery.objects.get_or_create(
        post=post,
        slug=BLOG_MAIN_GALLERY_SLUG,
        defaults={'title': 'Главная галерея', 'order': 0},
    )
    return gallery


def _serialize_blog_gallery_image(img):
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
def content_blog_gallery_upload(request, pk):
    post = _get_blog_post_for_user(request, pk)
    files = request.FILES.getlist('images')
    if not files:
        return JsonResponse({'error': 'No files'}, status=400)

    gallery = _get_or_create_main_gallery(post)
    max_order = gallery.images.aggregate(Max('order'))['order__max'] or 0
    for f in files:
        max_order += 10
        BlogGalleryImage.objects.create(
            gallery=gallery, image=normalize_uploaded_image(f), order=max_order,
        )

    items = [_serialize_blog_gallery_image(i) for i in gallery.images.all().order_by('order', 'pk')]
    return JsonResponse({'items': items})


@require_POST
@backoffice_required
def content_blog_gallery_reorder(request, pk):
    post = _get_blog_post_for_user(request, pk)
    try:
        payload = json.loads(request.body or '{}')
        order = list(payload.get('order') or [])
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    gallery = _get_or_create_main_gallery(post)
    own_ids = set(gallery.images.values_list('pk', flat=True))
    safe_order = [int(p) for p in order if int(p) in own_ids]
    for i, p in enumerate(safe_order):
        BlogGalleryImage.objects.filter(pk=p).update(order=i * 10)
    return JsonResponse({'ok': True})


@require_POST
@backoffice_required
def content_blog_gallery_update(request, pk, gpk):
    post = _get_blog_post_for_user(request, pk)
    img = get_object_or_404(BlogGalleryImage, pk=gpk, gallery__post=post)
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
    return JsonResponse({'ok': True, 'item': _serialize_blog_gallery_image(img)})


@require_POST
@backoffice_required
def content_blog_gallery_delete(request, pk, gpk):
    post = _get_blog_post_for_user(request, pk)
    img = get_object_or_404(BlogGalleryImage, pk=gpk, gallery__post=post)
    img.delete()
    return JsonResponse({'ok': True})


@require_POST
@backoffice_required
def content_blog_delete(request, pk):
    post = _get_blog_post_for_user(request, pk)
    title = post.title or f'Пост #{post.pk}'
    post.delete()
    messages.success(request, f'Пост «{title}» удалён.')
    return redirect('backoffice:content_blog_list')


@require_POST
@backoffice_required
def content_blog_seo(request, pk):
    _get_blog_post_for_user(request, pk)
    return run_seo(request, empty_hint='Заполни title и lead на RU.')


@require_POST
@backoffice_required
def content_blog_translate(request, pk):
    _get_blog_post_for_user(request, pk)
    return run_translate(request)


@require_POST
@backoffice_required
def content_blog_suggest_tags(request, pk):
    """POST {title, lead, content} → {tags: [{slug, name, is_new}]}.

    Сервер не использует значения из БД — менеджер мог поменять и не сохранить.
    Существующие теги берутся из БД (region-scoped); frontend помечает в UI
    пересечения как `existing` (синий чип) vs `new` (жёлтый чип).
    """
    post = _get_blog_post_for_user(request, pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    title = str(payload.get('title', ''))[:300]
    lead = str(payload.get('lead', ''))[:600]
    content = str(payload.get('content', ''))[:SUGGEST_TAGS_MAX_CONTENT]

    from django.utils.html import strip_tags
    content_text = strip_tags(content).strip()

    if not (title.strip() or lead.strip() or content_text):
        return JsonResponse({'error': 'Заполни title и хотя бы lead или content на RU.'}, status=400)

    existing = list(
        BlogTag.objects.filter(region=post.region)
        .order_by('order', 'name')
        .values('slug', 'name')
    )

    try:
        suggested = suggest_tags(
            title=title,
            lead=lead,
            content=content_text,
            existing_tags=existing,
        )
    except TranslationConfigError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except TranslationError as e:
        return JsonResponse({'error': str(e)}, status=502)

    existing_slug_set = {t['slug'] for t in existing}
    annotated = [
        {**t, 'is_new': t['slug'] not in existing_slug_set}
        for t in suggested
    ]
    return JsonResponse({'tags': annotated})


# ----- Blog taxonomy (categories + tags) -------------------------------------


@never_cache
@backoffice_required
@require_http_methods(['GET', 'POST'])
def content_blog_taxonomy(request):
    """Одна общая страница CRUD категорий и тегов. Глобальные (миграции 0006-0007).
    Order/slug не показываем."""
    categories = list(
        BlogCategory.objects
        .annotate(post_count=Count('posts'))
        .order_by('order', 'name')
    )
    tags = list(
        BlogTag.objects
        .annotate(post_count=Count('posts'))
        .order_by('order', 'name')
    )

    return render_backoffice(
        request,
        'backoffice/content/blog/taxonomy.html',
        active='blog',
        page_title='Блог · категории и теги',
        context={
            'categories': categories,
            'tags': tags,
        },
    )


def _taxonomy_save(model, model_label, request):
    """CRUD общая логика. Глобальные категории/теги — без region. Order auto:
    max+10 при создании, не меняется при update."""
    pk = request.POST.get('pk') or ''
    if pk:
        obj = get_object_or_404(model.objects.all(), pk=pk)
        for lang in TRANSLATION_LANGS:
            key = f'name_{lang}'
            if key in request.POST:
                setattr(obj, key, request.POST.get(key, '').strip()[:80])
        obj.name = obj.name_ru or obj.name or ''
        obj.save()
        messages.success(request, f'{model_label} «{obj.name}» обновлён(а).')
    else:
        name_ru = (request.POST.get('name_ru') or '').strip()
        if not name_ru:
            messages.error(request, 'Введите название.')
            return
        from django.utils.text import slugify
        from itertools import count
        base_slug = slugify(name_ru, allow_unicode=False) or 'tag'
        slug = base_slug[:60]
        for i in count(1):
            if not model.objects.filter(slug=slug).exists():
                break
            slug = f'{base_slug[:55]}-{i}'
        max_order = model.objects.aggregate(Max('order'))['order__max'] or 0
        obj = model.objects.create(
            slug=slug,
            name=name_ru[:80],
            name_ru=name_ru[:80],
            order=max_order + 10,
        )
        messages.success(request, f'{model_label} «{obj.name}» создан(а).')


@require_POST
@backoffice_required
def content_blog_category_save(request):
    _taxonomy_save(BlogCategory, 'Категория', request)
    return redirect('backoffice:content_blog_taxonomy')


@require_POST
@backoffice_required
def content_blog_tag_save(request):
    _taxonomy_save(BlogTag, 'Тег', request)
    return redirect('backoffice:content_blog_taxonomy')


@require_POST
@backoffice_required
def content_blog_category_delete(request, pk):
    cat = get_object_or_404(BlogCategory.objects.all(), pk=pk)
    if cat.posts.exists():
        messages.error(
            request,
            f'Нельзя удалить «{cat.name}» — в категории {cat.posts.count()} постов. '
            'Перенесите их в другую категорию сначала.',
        )
    else:
        name = cat.name
        cat.delete()
        messages.success(request, f'Категория «{name}» удалена.')
    return redirect('backoffice:content_blog_taxonomy')


@require_POST
@backoffice_required
def content_blog_tag_delete(request, pk):
    tag = get_object_or_404(BlogTag.objects.all(), pk=pk)
    name = tag.name
    tag.delete()  # M2M очистится автоматически
    messages.success(request, f'Тег «{name}» удалён.')
    return redirect('backoffice:content_blog_taxonomy')
