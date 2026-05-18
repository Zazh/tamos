import json

from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods, require_POST

from core.gemini_translate import (
    TranslationConfigError,
    TranslationError,
    generate_seo,
    suggest_tags,
    translate_fields,
)
from activities.models import (
    Activity,
    ActivityGroup,
    ActivitySection,
    ScheduleSlot,
)
from admission.models import (
    AdmissionPage,
    AdmissionVariant,
)
from blog.models import BlogCategory, BlogGallery, BlogGalleryImage, BlogPost, BlogTag
from team.models import TeamMember
from feedback.models import Lead
from pages.models import ContactsPage, HomeGalleryImage, HomePage
from programs.models import ProgramPage
from regions.models import Region

from .forms import (
    ACTIVITY_TRANSLATABLE,
    ActivityEditForm,
    ActivityGroupFormSet,
    ADMISSION_PAGE_INLINE_FORMSETS,
    ADMISSION_PAGE_TRANSLATABLE,
    ADMISSION_VARIANT_FIXED_SLOT_COUNT,
    ADMISSION_VARIANT_FIXED_SLOT_SECTIONS,
    ADMISSION_VARIANT_INLINE_FORMSETS,
    ADMISSION_VARIANT_TRANSLATABLE,
    AdmissionPageEditForm,
    AdmissionVariantEditForm,
    BLOG_POST_OUT_OF_FORM_BASES,
    BLOG_POST_TRANSLATABLE,
    BlogCategoryCreateForm,
    BlogPostEditForm,
    BlogTagCreateForm,
    CONTACTS_TRANSLATABLE,
    ContactsDepartmentFormSet,
    ContactsPageEditForm,
    HomePageEditForm,
    LeadEditForm,
    LoginForm,
    PROGRAM_FIXED_SLOT_COUNT,
    PROGRAM_FIXED_SLOT_SECTIONS,
    PROGRAM_INLINE_FORMSETS,
    PROGRAM_TRANSLATABLE,
    ProgramPageEditForm,
    ScheduleSlotFormSet,
    TRANSLATION_LANGS,
    HOME_TRANSLATABLE,
    TEAM_MEMBER_OUT_OF_FORM_BASES,
    TEAM_MEMBER_TRANSLATABLE,
    TeamMemberEditForm,
)
from .shortcuts import backoffice_required, region_scoped, render_backoffice


# ----- auth ----------------------------------------------------------------


@never_cache
@csrf_protect
@require_http_methods(['GET', 'POST'])
def login(request):
    """Backoffice login. Allows is_staff users only; superusers welcome."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('backoffice:dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        auth_login(request, form.get_user())
        next_url = request.POST.get('next') or request.GET.get('next')
        return redirect(next_url or reverse('backoffice:dashboard'))

    return render(request, 'backoffice/login.html', {'form': form})


@require_POST
def logout(request):
    auth_logout(request)
    return redirect('backoffice:login')


# ----- dashboard -----------------------------------------------------------


@never_cache
@backoffice_required
def dashboard(request):
    return render_backoffice(
        request,
        'backoffice/dashboard.html',
        active='dashboard',
        page_title='Дашборд',
    )


# ----- leads ---------------------------------------------------------------


LEADS_PER_PAGE = 25
LEAD_STATUSES = [
    ('', 'Все'),
    (Lead.Status.NEW, 'Новые'),
    (Lead.Status.IN_PROGRESS, 'В работе'),
    (Lead.Status.DONE, 'Закрыто'),
    (Lead.Status.REJECTED, 'Отказ'),
]


def _chip_url(request, status_value):
    """Линк для статус-чипа, сохраняющий остальные GET-параметры (q/category/region).

    Сбрасывает page — иначе после фильтра остаётся «странная» page=2 при пустом
    результате на 2-й странице.
    """
    qs = request.GET.copy()
    qs.pop('page', None)
    if status_value:
        qs['status'] = status_value
    else:
        qs.pop('status', None)
    encoded = qs.urlencode()
    base = reverse('backoffice:leads_list')
    return f'{base}?{encoded}' if encoded else base


@never_cache
@backoffice_required
def leads_list(request):
    base_qs = region_scoped(
        Lead.objects.select_related('region'),
        request.user,
    )

    # Счётчики по статусам — считаем ПО base_qs (region-scoped, без filter).
    counts_raw = dict(base_qs.values_list('status').annotate(c=Count('id')))
    counts = {
        'all': sum(counts_raw.values()),
        Lead.Status.NEW: counts_raw.get(Lead.Status.NEW, 0),
        Lead.Status.IN_PROGRESS: counts_raw.get(Lead.Status.IN_PROGRESS, 0),
        Lead.Status.DONE: counts_raw.get(Lead.Status.DONE, 0),
        Lead.Status.REJECTED: counts_raw.get(Lead.Status.REJECTED, 0),
    }

    # Применяем фильтры из GET.
    qs = base_qs

    status = request.GET.get('status', '').strip()
    if status in {Lead.Status.NEW, Lead.Status.IN_PROGRESS, Lead.Status.DONE, Lead.Status.REJECTED}:
        qs = qs.filter(status=status)

    category = request.GET.get('category', '').strip()
    if category in {c for c, _ in Lead.Category.choices}:
        qs = qs.filter(category=category)

    region_slug = request.GET.get('region', '').strip()
    if region_slug and request.user.is_superuser:
        qs = qs.filter(region__slug=region_slug)

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(phone__icontains=q)
            | Q(origin__icontains=q)
            | Q(title__icontains=q)
            | Q(city__icontains=q)
            | Q(manager_note__icontains=q)
        )

    paginator = Paginator(qs, LEADS_PER_PAGE)
    page = paginator.get_page(request.GET.get('page'))

    # Querystring без `page` — чтобы пагинатор сохранял остальные фильтры.
    qs_dict = request.GET.copy()
    qs_dict.pop('page', None)
    base_qs_str = qs_dict.urlencode()

    # Готовый список chip-данных с URL и счётчиком.
    status_chips = [
        {
            'code': code,
            'label': label,
            'count': counts['all'] if code == '' else counts.get(code, 0),
            'active': status == code,
            'url': _chip_url(request, code),
        }
        for code, label in LEAD_STATUSES
    ]

    return render_backoffice(
        request,
        'backoffice/leads/list.html',
        active='leads',
        page_title='Заявки',
        context={
            'page': page,
            'paginator': paginator,
            'status_chips': status_chips,
            'categories': Lead.Category.choices,
            'all_regions': Region.objects.filter(is_active=True) if request.user.is_superuser else None,
            'filters': {
                'status': status,
                'category': category,
                'region': region_slug,
                'q': q,
            },
            'base_qs': base_qs_str,
        },
    )


@never_cache
@backoffice_required
def lead_detail(request, pk):
    qs = region_scoped(Lead.objects.select_related('region'), request.user)
    lead = get_object_or_404(qs, pk=pk)

    if request.method == 'POST':
        form = LeadEditForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, 'Заявка обновлена.')
            return redirect('backoffice:lead_detail', pk=lead.pk)
    else:
        form = LeadEditForm(instance=lead)

    return render_backoffice(
        request,
        'backoffice/leads/detail.html',
        active='leads',
        page_title=f'Заявка #{lead.pk}',
        context={
            'lead': lead,
            'form': form,
            'STATUS': Lead.Status,
        },
    )


@require_POST
@backoffice_required
def lead_quick_status(request, pk):
    """Быстрая смена статуса с detail/list (POST с полем `status`)."""
    qs = region_scoped(Lead.objects.all(), request.user)
    lead = get_object_or_404(qs, pk=pk)

    new_status = request.POST.get('status', '')
    valid = {c for c, _ in Lead.Status.choices}
    if new_status not in valid:
        messages.error(request, 'Неизвестный статус.')
    elif lead.status == new_status:
        messages.info(request, 'Статус не изменился.')
    else:
        lead.status = new_status
        lead.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'Статус: {lead.get_status_display()}.')

    next_url = request.POST.get('next') or reverse('backoffice:lead_detail', kwargs={'pk': lead.pk})
    return redirect(next_url)


# ----- content (HomePage / ContactsPage) ------------------------------------
#
# Каждый раздел: list (региональные строки) + edit (singleton per region).
# Страницы создаются только через data-migration; backoffice их не создаёт.
# Менеджер видит только свой регион (region_scoped); superuser — все.


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
    """JSON-представление одной картинки галереи для frontend Alpine-компонента."""
    return {
        'pk': img.pk,
        'url': img.image.url if img.image else '',
        'orientation': img.orientation,
        'order': img.order,
        'alt_text_ru': img.alt_text_ru or '',
        'alt_text_kk': img.alt_text_kk or '',
        'alt_text_en': img.alt_text_en or '',
    }


_strict_zip_arrange = HomeGalleryImage.strict_zip_arrange  # alias (старое имя)


def _homepage_steps(home):
    """Описание шагов заполнения HomePage для completeness-stepper в edit-форме.

    Каждый шаг — dict с `fields` (имена form-инпутов), `filled` (сколько уже
    заполнено на сервере). Frontend (`boFormSteps` Alpine) пересчитывает
    `filled` на лету по input-событиям. Если у шага `required=True` и
    `filled < total` — кнопка Save disabled.

    Поля file-типа в `filled` проверяются по присутствию на сервере: если на
    инстансе уже есть, то filled=True (даже если в input новый файл не выбран).
    Шаг «Шоурил» помечен `optional` — менеджеру не обязательно его заполнять,
    но stepper всё равно показывает прогресс.
    """
    def is_filled(field_name):
        # form-name → instance attr (для translatable: hero_title_ru → hero_title_ru)
        val = getattr(home, field_name, '')
        if hasattr(val, 'name'):  # FieldFile/ImageField
            return bool(val and val.name)
        return bool(val and str(val).strip())

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

    def step(id, label, fields, required=False):
        initial = {f: is_filled(f) for f in fields}
        filled = sum(1 for v in initial.values() if v)
        return {
            'id': id,
            'label': label,
            'fields': fields,
            'initial': initial,
            'filled': filled,
            'total': len(fields),
            'required': required,
        }

    return [
        step('ru', 'Основа (RU)', ru_fields, required=True),
        step('kk', 'Перевод KZ', kk_fields),
        step('en', 'Перевод EN', en_fields),
        step('seo', 'SEO', seo_fields),
        step('video', 'Шоурил', video_fields),
    ]


def _human_size(num_bytes):
    """`1234567` → `'1.2 MB'`."""
    if num_bytes is None:
        return ''
    for unit in ('B', 'KB', 'MB', 'GB'):
        if num_bytes < 1024:
            return f'{num_bytes:.1f} {unit}' if unit != 'B' else f'{num_bytes} B'
        num_bytes /= 1024
    return f'{num_bytes:.1f} TB'


@never_cache
@backoffice_required
def content_home_edit(request, pk):
    qs = region_scoped(HomePage.objects.select_related('region'), request.user)
    home = get_object_or_404(qs, pk=pk)

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
    """region-scoped HomePage или 404."""
    qs = region_scoped(HomePage.objects.all(), request.user)
    return get_object_or_404(qs, pk=pk)


@require_POST
@backoffice_required
def content_home_gallery_upload(request, pk):
    """Multi-upload новых картинок. orientation определяется в save() модели,
    после — весь список (старые+новые) расставляется strict-zip-ом, order
    пересохраняется с шагом 10."""
    home = _get_home_for_user(request, pk)
    files = request.FILES.getlist('images')
    if not files:
        return JsonResponse({'error': 'No files'}, status=400)

    for f in files:
        HomeGalleryImage.objects.create(home_page=home, image=f, order=9999)

    # Strict-zip reorder всего списка
    arranged = _strict_zip_arrange(home.gallery.all())
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


# ----- auto-translate -------------------------------------------------------
#
# Gemini-based авто-перевод пустых KK/EN translatable-полей. Сервер не пишет
# в БД — возвращает переведённые значения, клиент заполняет инпуты, менеджер
# смотрит и сабмитит общую форму сам.

# Защита от мусорных payload'ов и слишком длинных значений.
TRANSLATE_MAX_FIELDS_PER_LANG = 30
TRANSLATE_MAX_VALUE_CHARS = 5000


@require_POST
@backoffice_required
def content_home_translate(request, pk):
    """POST {by_lang: {kk: {field: ru_text, ...}, en: {...}}} →
       {translations: {kk: {field: text}, en: {field: text}}}.

    Region-scope обязательный (404 на чужой регион). Сам HomePage только
    для авторизации — сервер не использует значения из БД, только из payload
    (менеджер мог изменить RU и ещё не сохранить).
    """
    _get_home_for_user(request, pk)  # 404 если не в region-scope

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    by_lang = payload.get('by_lang') or {}
    if not isinstance(by_lang, dict):
        return JsonResponse({'error': 'by_lang must be an object'}, status=400)

    result: dict[str, dict[str, str]] = {}
    for lang, values in by_lang.items():
        if lang not in {'kk', 'en'}:
            continue
        if not isinstance(values, dict):
            continue
        sanitized = {
            str(k): str(v)[:TRANSLATE_MAX_VALUE_CHARS]
            for k, v in list(values.items())[:TRANSLATE_MAX_FIELDS_PER_LANG]
            if v and str(v).strip()
        }
        if not sanitized:
            continue
        try:
            result[lang] = translate_fields(sanitized, lang)
        except TranslationConfigError as e:
            return JsonResponse({'error': str(e)}, status=503)
        except TranslationError as e:
            return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'translations': result})


SEO_SOURCE_MAX_FIELDS = 12
SEO_SOURCE_MAX_CHARS = 8000


@require_POST
@backoffice_required
def content_home_seo(request, pk):
    """POST {content: {field: ru_text, ...}} → {seo: {lang: {seo_field: text}}}.

    Сервер не использует значения из БД — берёт всё из payload (менеджер мог
    править RU и ещё не сохранить). Region-scope обязательный.
    """
    _get_home_for_user(request, pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    content = payload.get('content') or {}
    if not isinstance(content, dict):
        return JsonResponse({'error': 'content must be an object'}, status=400)

    sanitized = {
        str(k): str(v)[:SEO_SOURCE_MAX_CHARS]
        for k, v in list(content.items())[:SEO_SOURCE_MAX_FIELDS]
        if v and str(v).strip()
    }
    if not sanitized:
        return JsonResponse({'error': 'Нет исходного контента для SEO. Заполни хотя бы hero_title/about_body на RU.'}, status=400)

    try:
        seo = generate_seo(sanitized)
    except TranslationConfigError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except TranslationError as e:
        return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'seo': seo})


@never_cache
@backoffice_required
def content_contacts_list(request):
    qs = (
        region_scoped(ContactsPage.objects.select_related('region'), request.user)
        .annotate(department_count=Count('departments'))
        .order_by('region__name')
    )
    return render_backoffice(
        request,
        'backoffice/content/contacts/list.html',
        active='contacts',
        page_title='Контакты',
        context={'rows': qs},
    )


def _get_contacts_for_user(request, pk):
    """region-scoped ContactsPage или 404."""
    qs = region_scoped(ContactsPage.objects.all(), request.user)
    return get_object_or_404(qs, pk=pk)


def _contactspage_steps(contacts, formset=None):
    """Шаги stepper'а для completeness на edit-странице ContactsPage.

    Шаги:
    - Основа RU (обязательный): intro + office + map (lat/lng + zoom).
    - Перевод KZ / EN: те же intro+office (без map — координаты language-neutral).
    - SEO (опц): seo/og поля на RU.
    - Отделы: считаем сколько отделов имеют непустые title+description+phone+email.
    """
    def is_filled(field_name):
        val = getattr(contacts, field_name, '')
        if hasattr(val, 'name'):
            return bool(val and val.name)
        return bool(val and str(val).strip())

    ru_fields = [
        'intro_title_ru',
        'intro_text_ru',
        'office_name_ru',
        'office_address_ru',
        'office_hours_ru',
        'latitude',
        'longitude',
    ]
    kk_fields = [
        'intro_title_kk', 'intro_text_kk',
        'office_name_kk', 'office_address_kk', 'office_hours_kk',
    ]
    en_fields = [
        'intro_title_en', 'intro_text_en',
        'office_name_en', 'office_address_en', 'office_hours_en',
    ]
    seo_fields = [
        'seo_title_ru', 'seo_description_ru', 'og_title_ru', 'og_description_ru',
    ]

    def step(id, label, fields, required=False):
        initial = {f: is_filled(f) for f in fields}
        filled = sum(1 for v in initial.values() if v)
        return {
            'id': id,
            'label': label,
            'fields': fields,
            'initial': initial,
            'filled': filled,
            'total': len(fields),
            'required': required,
        }

    # Departments — считаем по живым (не помеченным DELETE и не пустым) формам.
    # Этот шаг — read-only счётчик: stepper не отслеживает изменения формсета
    # на лету (departments — inline formset, его pk-структуру JS не знает).
    dept_total = contacts.departments.count()
    dept_filled = sum(
        1 for d in contacts.departments.all()
        if (d.title or '').strip() and (d.description or '').strip()
        and ((d.phone or '').strip() or (d.email or '').strip())
    )

    return [
        step('ru', 'Основа (RU)', ru_fields, required=True),
        step('kk', 'Перевод KZ', kk_fields),
        step('en', 'Перевод EN', en_fields),
        step('seo', 'SEO', seo_fields),
        {
            'id': 'departments',
            'label': 'Отделы',
            'fields': [],
            'initial': {},
            'filled': dept_filled,
            'total': dept_total or 1,  # избегаем 0/0 — показываем «0/1»
            'required': False,
            'readonly': True,
        },
    ]


@never_cache
@backoffice_required
def content_contacts_edit(request, pk):
    contacts = _get_contacts_for_user(request, pk)

    if request.method == 'POST':
        form = ContactsPageEditForm(request.POST, request.FILES, instance=contacts)
        formset = ContactsDepartmentFormSet(request.POST, instance=contacts, prefix='departments')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Страница «Контакты» сохранена.')
            return redirect('backoffice:content_contacts_edit', pk=contacts.pk)
    else:
        form = ContactsPageEditForm(instance=contacts)
        formset = ContactsDepartmentFormSet(instance=contacts, prefix='departments')

    steps = _contactspage_steps(contacts, formset)

    # Bases для inline-departments auto-translate. Каждая форма формсета имеет
    # отдельный prefix `departments-N-*`, frontend Alpine-компонент находит их
    # по data-form-id + data-prefix.
    department_translatable_bases = ['title', 'description', 'hours']

    return render_backoffice(
        request,
        'backoffice/content/contacts/edit.html',
        active='contacts',
        page_title=f'Контакты — {contacts.region.name}',
        context={
            'contacts': contacts,
            'form': form,
            'formset': formset,
            'translation_langs': TRANSLATION_LANGS,
            'steps_json': json.dumps(steps),
            'translatable_bases_json': json.dumps(list(CONTACTS_TRANSLATABLE)),
            'department_translatable_bases_json': json.dumps(department_translatable_bases),
        },
    )


@require_POST
@backoffice_required
def content_contacts_translate(request, pk):
    """RU→KK/EN перевод для ContactsPage через Gemini. Структура payload
    идентична `content_home_translate` — менеджер мог поменять RU и не сохранить,
    сервер берёт значения из payload (не из БД).

    Используется и для основной формы (intro/office/SEO), и для каждого
    department отдельно. По имени поля сервер не различает — просто переводит
    словарь `{name: ru_text}`.
    """
    _get_contacts_for_user(request, pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    by_lang = payload.get('by_lang') or {}
    if not isinstance(by_lang, dict):
        return JsonResponse({'error': 'by_lang must be an object'}, status=400)

    result: dict[str, dict[str, str]] = {}
    for lang, values in by_lang.items():
        if lang not in {'kk', 'en'}:
            continue
        if not isinstance(values, dict):
            continue
        sanitized = {
            str(k): str(v)[:TRANSLATE_MAX_VALUE_CHARS]
            for k, v in list(values.items())[:TRANSLATE_MAX_FIELDS_PER_LANG]
            if v and str(v).strip()
        }
        if not sanitized:
            continue
        try:
            result[lang] = translate_fields(sanitized, lang)
        except TranslationConfigError as e:
            return JsonResponse({'error': str(e)}, status=503)
        except TranslationError as e:
            return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'translations': result})


@require_POST
@backoffice_required
def content_contacts_seo(request, pk):
    """AI-генерация SEO/OG для ContactsPage. Использует intro_title/intro_text
    + office_name/office_address как источник (передаются в payload, не из БД)."""
    _get_contacts_for_user(request, pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    content = payload.get('content') or {}
    if not isinstance(content, dict):
        return JsonResponse({'error': 'content must be an object'}, status=400)

    sanitized = {
        str(k): str(v)[:SEO_SOURCE_MAX_CHARS]
        for k, v in list(content.items())[:SEO_SOURCE_MAX_FIELDS]
        if v and str(v).strip()
    }
    if not sanitized:
        return JsonResponse(
            {'error': 'Нет исходного контента для SEO. Заполни хотя бы intro_title/intro_text на RU.'},
            status=400,
        )

    try:
        seo = generate_seo(sanitized)
    except TranslationConfigError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except TranslationError as e:
        return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'seo': seo})


# ----- content: AdmissionPage / AdmissionVariant ----------------------------
#
# AdmissionPage edit — общие тексты + 2 inline (included_items, documents) + grid
# с превью 6 вариантов (ссылки на отдельные edit-страницы).
# AdmissionVariant edit — hero + leads этапов + testing-features (fixed 4) +
# pricing-plans (гибкое количество) + SEO/OG.
#
# Region-scope:
#   AdmissionPage  — region_scoped(qs, user) по полю region (FK напрямую)
#   AdmissionVariant — region на page; фильтр через page__region (через
#                       region_scoped с region_field='page__region')


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
    """region-scoped AdmissionPage или 404."""
    qs = region_scoped(AdmissionPage.objects.all(), request.user)
    return get_object_or_404(qs, pk=pk)


def _get_admission_variant_for_user(request, vpk):
    """region-scoped AdmissionVariant (через page__region) или 404."""
    qs = region_scoped(
        AdmissionVariant.objects.select_related('page__region', 'department', 'grade'),
        request.user,
        region_field='page__region',
    )
    return get_object_or_404(qs, pk=vpk)


def _admissionpage_steps(page, formsets):
    """Шаги stepper'а completeness на edit-странице AdmissionPage.

    - Основа RU (обязательный): stepper titles + section titles + UI labels + testing rules + enrollment + consultation.
    - Перевод KZ / EN — те же ключевые поля.
    - Inline: read-only счётчик (included + documents).
    """
    def is_filled(field_name):
        val = getattr(page, field_name, '')
        if hasattr(val, 'name'):
            return bool(val and val.name)
        return bool(val and str(val).strip())

    # Ключевой набор полей (не каждый — иначе шумно).
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

    def step(id, label, fields, required=False):
        initial = {f: is_filled(f) for f in fields}
        filled = sum(1 for v in initial.values() if v)
        return {
            'id': id,
            'label': label,
            'fields': fields,
            'initial': initial,
            'filled': filled,
            'total': len(fields),
            'required': required,
        }

    inline_total = page.included_items.count() + page.documents.count()
    return [
        step('ru', 'Основа (RU)', ru_fields, required=True),
        step('kk', 'Перевод KZ', kk_fields),
        step('en', 'Перевод EN', en_fields),
        {
            'id': 'inline',
            'label': 'Списки',
            'fields': [],
            'initial': {},
            'filled': inline_total,
            'total': inline_total or 1,
            'required': False,
            'readonly': True,
        },
    ]


@never_cache
@backoffice_required
def content_admission_edit(request, pk):
    """Edit AdmissionPage (общие тексты) + 2 inline + grid 6 вариантов внизу."""
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

    # Превью 6 вариантов (RU 1/2-7/8-11 + KZ 1/2-6/7-11) с счётчиком заполненности.
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

    steps = _admissionpage_steps(page, formsets)

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
    """RU→KK/EN перевод для AdmissionPage (и его inline included/documents)."""
    _get_admission_for_user(request, pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    by_lang = payload.get('by_lang') or {}
    if not isinstance(by_lang, dict):
        return JsonResponse({'error': 'by_lang must be an object'}, status=400)

    result: dict[str, dict[str, str]] = {}
    for lang, values in by_lang.items():
        if lang not in {'kk', 'en'}:
            continue
        if not isinstance(values, dict):
            continue
        sanitized = {
            str(k): str(v)[:TRANSLATE_MAX_VALUE_CHARS]
            for k, v in list(values.items())[:TRANSLATE_MAX_FIELDS_PER_LANG]
            if v and str(v).strip()
        }
        if not sanitized:
            continue
        try:
            result[lang] = translate_fields(sanitized, lang)
        except TranslationConfigError as e:
            return JsonResponse({'error': str(e)}, status=503)
        except TranslationError as e:
            return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'translations': result})


def _ensure_admission_fixed_sections(variant):
    """Гарантирует 4 testing_features на variant. См. _ensure_program_fixed_sections."""
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


def _admissionvariant_steps(variant, formsets):
    """Шаги для variant edit:
    - RU (обязательный): h1 + hero_lead + leads этапов
    - KK/EN: те же
    - SEO (опц)
    - Inline: read-only счётчик (testing + pricing)
    """
    def is_filled(field_name):
        val = getattr(variant, field_name, '')
        if hasattr(val, 'name'):
            return bool(val and val.name)
        return bool(val and str(val).strip())

    ru_fields = [
        'h1_ru', 'hero_lead_ru',
        'testing_lead_ru', 'result_intro_ru', 'result_detail_ru', 'pricing_lead_ru',
    ]
    kk_fields = [f.replace('_ru', '_kk') for f in ru_fields]
    en_fields = [f.replace('_ru', '_en') for f in ru_fields]
    seo_fields = ['seo_title_ru', 'seo_description_ru', 'og_title_ru', 'og_description_ru']

    def step(id, label, fields, required=False):
        initial = {f: is_filled(f) for f in fields}
        filled = sum(1 for v in initial.values() if v)
        return {
            'id': id,
            'label': label,
            'fields': fields,
            'initial': initial,
            'filled': filled,
            'total': len(fields),
            'required': required,
        }

    inline_total = variant.testing_features.count() + variant.pricing_plans.count()
    return [
        step('ru', 'Основа (RU)', ru_fields, required=True),
        step('kk', 'Перевод KZ', kk_fields),
        step('en', 'Перевод EN', en_fields),
        step('seo', 'SEO', seo_fields),
        {
            'id': 'inline',
            'label': 'Карточки',
            'fields': [],
            'initial': {},
            'filled': inline_total,
            'total': inline_total or 1,
            'required': False,
            'readonly': True,
        },
    ]


@never_cache
@backoffice_required
def content_admission_variant_edit(request, vpk):
    """Edit одного варианта (dept × grade)."""
    variant = _get_admission_variant_for_user(request, vpk)

    # Гарантируем 4 testing-features до инициализации formset'а.
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

    steps = _admissionvariant_steps(variant, formsets)

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
    """RU→KK/EN перевод для AdmissionVariant (включая SEO и inline testing/pricing)."""
    _get_admission_variant_for_user(request, vpk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    by_lang = payload.get('by_lang') or {}
    if not isinstance(by_lang, dict):
        return JsonResponse({'error': 'by_lang must be an object'}, status=400)

    result: dict[str, dict[str, str]] = {}
    for lang, values in by_lang.items():
        if lang not in {'kk', 'en'}:
            continue
        if not isinstance(values, dict):
            continue
        sanitized = {
            str(k): str(v)[:TRANSLATE_MAX_VALUE_CHARS]
            for k, v in list(values.items())[:TRANSLATE_MAX_FIELDS_PER_LANG]
            if v and str(v).strip()
        }
        if not sanitized:
            continue
        try:
            result[lang] = translate_fields(sanitized, lang)
        except TranslationConfigError as e:
            return JsonResponse({'error': str(e)}, status=503)
        except TranslationError as e:
            return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'translations': result})


@require_POST
@backoffice_required
def content_admission_variant_seo(request, vpk):
    """AI-генерация SEO/OG для variant'а. Источник — h1/hero_lead/pricing_lead."""
    _get_admission_variant_for_user(request, vpk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    content = payload.get('content') or {}
    if not isinstance(content, dict):
        return JsonResponse({'error': 'content must be an object'}, status=400)

    sanitized = {
        str(k): str(v)[:SEO_SOURCE_MAX_CHARS]
        for k, v in list(content.items())[:SEO_SOURCE_MAX_FIELDS]
        if v and str(v).strip()
    }
    if not sanitized:
        return JsonResponse(
            {'error': 'Нет исходного контента для SEO. Заполни h1/hero_lead на RU.'},
            status=400,
        )

    try:
        seo = generate_seo(sanitized)
    except TranslationConfigError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except TranslationError as e:
        return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'seo': seo})


# ----- content: ProgramPage --------------------------------------------------


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
    """region-scoped ProgramPage или 404."""
    qs = region_scoped(ProgramPage.objects.all(), request.user)
    return get_object_or_404(qs, pk=pk)


def _programpage_steps(program, formsets):
    """Шаги stepper'а completeness на edit-странице ProgramPage.

    - Основа RU (обязательный): hero + лейблы/заголовки секций (только ключевое,
      не каждое поле, иначе 30+ полей в чек-листе).
    - Перевод KZ / EN — те же поля что в RU.
    - SEO (опц): seo/og поля на RU.
    - Inline — read-only счётчик: суммарное число живых элементов по 7 inline'ам.
    """
    def is_filled(field_name):
        val = getattr(program, field_name, '')
        if hasattr(val, 'name'):
            return bool(val and val.name)
        return bool(val and str(val).strip())

    # Ключевой набор полей для completeness (не каждый текстовый — иначе шумно).
    ru_fields = [
        'hero_badge_text_ru',
        'hero_title_ru',
        'hero_subtitle_ru',
        'hero_cta_primary_text_ru',
        'hero_cta_secondary_text_ru',
        'audience_label_ru',
        'audience_title_ru',
        'benefits_label_ru',
        'benefits_title_ru',
        'programs_label_ru',
        'programs_title_ru',
        'team_label_ru',
        'team_title_ru',
        'certificate_label_ru',
        'certificate_title_ru',
        'activities_label_ru',
        'activities_title_ru',
        'stats_label_ru',
        'stats_title_ru',
        'faq_label_ru',
        'faq_title_ru',
    ]
    # KK/EN — те же поля с другим суффиксом.
    kk_fields = [f.replace('_ru', '_kk') for f in ru_fields]
    en_fields = [f.replace('_ru', '_en') for f in ru_fields]

    seo_fields = [
        'seo_title_ru', 'seo_description_ru', 'og_title_ru', 'og_description_ru',
    ]

    def step(id, label, fields, required=False):
        initial = {f: is_filled(f) for f in fields}
        filled = sum(1 for v in initial.values() if v)
        return {
            'id': id,
            'label': label,
            'fields': fields,
            'initial': initial,
            'filled': filled,
            'total': len(fields),
            'required': required,
        }

    # Inline-секция: count живых элементов по 7 inline'ам (для информации).
    inline_total = 0
    inline_filled = 0
    for prefix, _cls, related_name, _label, _bases in PROGRAM_INLINE_FORMSETS:
        qs = getattr(program, related_name).all()
        inline_total += qs.count()
        inline_filled += qs.count()  # На сервере «заполненные» = существующие — JS не отслеживает.

    return [
        step('ru', 'Основа (RU)', ru_fields, required=True),
        step('kk', 'Перевод KZ', kk_fields),
        step('en', 'Перевод EN', en_fields),
        step('seo', 'SEO', seo_fields),
        {
            'id': 'inline',
            'label': 'Карточки',
            'fields': [],
            'initial': {},
            'filled': inline_filled,
            'total': inline_total or 1,
            'required': False,
            'readonly': True,
        },
    ]


def _ensure_program_fixed_sections(program):
    """Гарантирует, что у программы есть ровно PROGRAM_FIXED_SLOT_COUNT (=4)
    строк в каждой «фиксированной» секции (audience / benefit / cert / stat).

    Если строк меньше — создаёт пустые placeholder'ы (модельная валидация на
    .create() не срабатывает; форма уже отмечает поля как `required=False`).
    Если строк больше — оставляет как есть (max_num=4 в формсете блокирует
    добавление новых через UI).

    Вызывается перед инициализацией formset'а, поэтому свежесозданные строки
    сразу попадают в BoundForm'ы и редактируются менеджером.
    """
    for related_name, model in PROGRAM_FIXED_SLOT_SECTIONS:
        qs = getattr(program, related_name)
        existing = qs.count()
        if existing >= PROGRAM_FIXED_SLOT_COUNT:
            continue
        # Узнаём максимальный order, чтобы новые шли в конец списка
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

    # Создаём formset'ы по конфигурации PROGRAM_INLINE_FORMSETS — единое место правды.
    if request.method == 'POST':
        form = ProgramPageEditForm(request.POST, request.FILES, instance=program)
        formsets = [
            (prefix, formset_cls(request.POST, request.FILES, instance=program, prefix=prefix), related_name, label, bases)
            for prefix, formset_cls, related_name, label, bases in PROGRAM_INLINE_FORMSETS
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
            (prefix, formset_cls(instance=program, prefix=prefix), related_name, label, bases)
            for prefix, formset_cls, related_name, label, bases in PROGRAM_INLINE_FORMSETS
        ]

    steps = _programpage_steps(program, formsets)

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
    """RU→KK/EN перевод для ProgramPage через Gemini. Структура payload идентична
    content_home_translate / content_contacts_translate.

    Используется и для основной формы (hero/sections/SEO), и для каждого inline
    элемента отдельно (prefix-aware на клиенте, сервер просто переводит словарь).
    """
    _get_program_for_user(request, pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    by_lang = payload.get('by_lang') or {}
    if not isinstance(by_lang, dict):
        return JsonResponse({'error': 'by_lang must be an object'}, status=400)

    result: dict[str, dict[str, str]] = {}
    for lang, values in by_lang.items():
        if lang not in {'kk', 'en'}:
            continue
        if not isinstance(values, dict):
            continue
        sanitized = {
            str(k): str(v)[:TRANSLATE_MAX_VALUE_CHARS]
            for k, v in list(values.items())[:TRANSLATE_MAX_FIELDS_PER_LANG]
            if v and str(v).strip()
        }
        if not sanitized:
            continue
        try:
            result[lang] = translate_fields(sanitized, lang)
        except TranslationConfigError as e:
            return JsonResponse({'error': str(e)}, status=503)
        except TranslationError as e:
            return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'translations': result})


@require_POST
@backoffice_required
def content_program_seo(request, pk):
    """AI-генерация SEO/OG для ProgramPage. Использует hero_title/hero_subtitle
    + audience_title/benefits_title как источник (передаётся в payload, не из БД)."""
    _get_program_for_user(request, pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    content = payload.get('content') or {}
    if not isinstance(content, dict):
        return JsonResponse({'error': 'content must be an object'}, status=400)

    sanitized = {
        str(k): str(v)[:SEO_SOURCE_MAX_CHARS]
        for k, v in list(content.items())[:SEO_SOURCE_MAX_FIELDS]
        if v and str(v).strip()
    }
    if not sanitized:
        return JsonResponse(
            {'error': 'Нет исходного контента для SEO. Заполни hero_title/hero_subtitle на RU.'},
            status=400,
        )

    try:
        seo = generate_seo(sanitized)
    except TranslationConfigError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except TranslationError as e:
        return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'seo': seo})


# ----- content: Activities (Activity + Group + ScheduleSlot) ---------------
#
# Структура страниц (после редизайна 2026-05-18):
#   /backoffice/content/activities/                    — list регионов
#   /backoffice/content/activities/region/<region>/    — catalog: список
#                                                        collapsible-аккордеонов;
#                                                        каждый аккордеон содержит
#                                                        full form Activity + список
#                                                        ссылок на группы.
#   /backoffice/content/activities/<activity>/save/    — POST save (из аккордеона)
#   /backoffice/content/activities/<activity>/delete/  — POST delete
#   /backoffice/content/activities/<activity>/translate/ — RU→KK/EN
#   /backoffice/content/activities/group/<g>/          — edit Group + ScheduleSlot inline
#   /backoffice/content/activities/group/<g>/delete/   — POST delete
#
# Тренер хранится в строках на Activity (teacher_name/teacher_phone/teacher_bio).
# Отдельной модели Teacher больше НЕТ.


def _get_region_for_user(request, region_pk):
    """region-scoped Region или 404. Менеджер видит только свой регион."""
    from django.http import Http404
    region = get_object_or_404(Region.objects.filter(is_active=True), pk=region_pk)
    if request.user.is_superuser:
        return region
    if getattr(request.user, 'manager_region_id', None) == region.pk:
        return region
    raise Http404()


def _get_activity_for_user(request, pk):
    qs = region_scoped(
        Activity.objects.select_related('region', 'section'),
        request.user,
    )
    return get_object_or_404(qs, pk=pk)


def _get_group_for_user(request, gpk):
    """ActivityGroup, фильтрованная через activity__region."""
    qs = region_scoped(
        ActivityGroup.objects.select_related('activity__region', 'activity__section'),
        request.user,
        region_field='activity__region',
    )
    return get_object_or_404(qs, pk=gpk)


@never_cache
@backoffice_required
def content_activities_list(request):
    """Таблица регионов со счётчиком activities."""
    regions = (
        Region.objects.filter(is_active=True)
        .annotate(activity_count=Count('activities', distinct=True))
        .order_by('name')
    )
    if not request.user.is_superuser:
        if getattr(request.user, 'manager_region_id', None):
            regions = regions.filter(pk=request.user.manager_region_id)
        else:
            regions = regions.none()

    return render_backoffice(
        request,
        'backoffice/content/activities/list.html',
        active='activities',
        page_title='Активности',
        context={'rows': list(regions)},
    )


@never_cache
@backoffice_required
def content_activities_region(request, region_pk):
    """Catalog кружков региона по секциям. Каждый кружок — collapsible
    аккордеон с inline-формой ActivityEditForm и списком ссылок на группы.

    Сохранение каждого кружка — POST на content_activities_save (отдельный
    endpoint), не один общий submit на всю страницу.
    """
    region = _get_region_for_user(request, region_pk)

    activities = list(
        Activity.objects
        .filter(region=region)
        .select_related('section')
        .prefetch_related('groups__schedule_slots')
        .order_by('section__order', 'order', 'name')
    )

    sections = list(ActivitySection.objects.order_by('order', 'slug'))
    by_section = {s.pk: [] for s in sections}
    for a in activities:
        by_section[a.section_id].append(a)

    activity_forms = {
        a.pk: ActivityEditForm(instance=a, prefix=f'a{a.pk}')
        for a in activities
    }

    buckets = [
        {'section': s, 'activities': by_section.get(s.pk, [])}
        for s in sections
    ]

    return render_backoffice(
        request,
        'backoffice/content/activities/region.html',
        active='activities',
        page_title=f'Активности — {region.name}',
        context={
            'region': region,
            'buckets': buckets,
            'sections': sections,
            'activity_forms': activity_forms,
            'activity_count': len(activities),
            'translation_langs': TRANSLATION_LANGS,
            'translatable_bases_json': json.dumps(list(ACTIVITY_TRANSLATABLE)),
        },
    )


@require_POST
@backoffice_required
def content_activities_save(request, pk):
    """POST save одного кружка из аккордеона. После save — редирект на catalog."""
    activity = _get_activity_for_user(request, pk)
    form = ActivityEditForm(request.POST, instance=activity, prefix=f'a{activity.pk}')
    if form.is_valid():
        form.save()
        messages.success(request, f'Кружок «{activity.name}» сохранён.')
    else:
        err_msg = '; '.join(
            f'{name}: {", ".join(errs)}' for name, errs in form.errors.items()
        )[:300]
        messages.error(request, f'Ошибки в форме кружка #{activity.pk}: {err_msg}')

    url = reverse('backoffice:content_activities_region', kwargs={'region_pk': activity.region_id})
    return redirect(f'{url}#activity-{activity.pk}')


@require_POST
@backoffice_required
def content_activities_activity_add(request, region_pk):
    """POST: создать пустую Activity в регионе+секции, редирект на catalog с anchor."""
    region = _get_region_for_user(request, region_pk)
    section_pk = request.POST.get('section', '').strip()
    try:
        section = ActivitySection.objects.get(pk=int(section_pk))
    except (ValueError, ActivitySection.DoesNotExist):
        messages.error(request, 'Не указана секция.')
        return redirect('backoffice:content_activities_region', region_pk=region.pk)

    max_order = (
        Activity.objects.filter(region=region, section=section)
        .aggregate(_m=Max('order'))['_m'] or 0
    )
    activity = Activity.objects.create(
        region=region,
        section=section,
        name='Новый кружок',
        name_ru='Новый кружок',
        order=max_order + 10,
        is_published=False,
    )
    messages.success(request, 'Кружок создан. Заполни поля и сохрани.')
    url = reverse('backoffice:content_activities_region', kwargs={'region_pk': region.pk})
    return redirect(f'{url}#activity-{activity.pk}')


@require_POST
@backoffice_required
def content_activities_activity_delete(request, pk):
    """POST: удалить Activity + редирект на catalog региона."""
    activity = _get_activity_for_user(request, pk)
    region_pk = activity.region_id
    name = activity.name
    activity.delete()
    messages.success(request, f'Кружок «{name}» удалён.')
    return redirect('backoffice:content_activities_region', region_pk=region_pk)


@require_POST
@backoffice_required
def content_activities_reorder(request, region_pk):
    """AJAX: сохранить DnD-порядок activities внутри секции."""
    region = _get_region_for_user(request, region_pk)
    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        section_pk = int(payload.get('section_pk') or 0)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid section_pk'}, status=400)

    order = payload.get('order') or []
    if not isinstance(order, list):
        return JsonResponse({'error': 'order must be a list'}, status=400)

    own_ids = set(
        Activity.objects.filter(region=region, section_id=section_pk)
        .values_list('pk', flat=True)
    )
    safe_order = [int(p) for p in order if int(p) in own_ids]
    for i, pk_ in enumerate(safe_order):
        Activity.objects.filter(pk=pk_).update(order=i * 10)
    return JsonResponse({'ok': True})


@require_POST
@backoffice_required
def content_activities_translate(request, pk):
    """RU→KK/EN перевод для Activity (name/description/location/teacher_name/teacher_bio)."""
    _get_activity_for_user(request, pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    by_lang = payload.get('by_lang') or {}
    if not isinstance(by_lang, dict):
        return JsonResponse({'error': 'by_lang must be an object'}, status=400)

    result: dict[str, dict[str, str]] = {}
    for lang, values in by_lang.items():
        if lang not in {'kk', 'en'}:
            continue
        if not isinstance(values, dict):
            continue
        sanitized = {
            str(k): str(v)[:TRANSLATE_MAX_VALUE_CHARS]
            for k, v in list(values.items())[:TRANSLATE_MAX_FIELDS_PER_LANG]
            if v and str(v).strip()
        }
        if not sanitized:
            continue
        try:
            result[lang] = translate_fields(sanitized, lang)
        except TranslationConfigError as e:
            return JsonResponse({'error': str(e)}, status=503)
        except TranslationError as e:
            return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'translations': result})


# ----- Group edit (отдельная страница, ScheduleSlot inline) ----------------


@require_POST
@backoffice_required
def content_activities_group_add(request, pk):
    """POST: создать пустую группу для Activity, редирект на edit Group."""
    activity = _get_activity_for_user(request, pk)
    max_order = (
        ActivityGroup.objects.filter(activity=activity).aggregate(_m=Max('order'))['_m'] or 0
    )
    group = ActivityGroup.objects.create(activity=activity, order=max_order + 10)
    messages.success(request, 'Группа создана. Задай классы, цену и расписание.')
    return redirect('backoffice:content_activities_group_edit', gpk=group.pk)


@never_cache
@backoffice_required
def content_activities_group_edit(request, gpk):
    """Edit одной группы + inline ScheduleSlot formset."""
    from .forms import ActivityGroupForm

    group = _get_group_for_user(request, gpk)
    activity = group.activity

    if request.method == 'POST':
        form = ActivityGroupForm(request.POST, instance=group)
        slot_fs = ScheduleSlotFormSet(request.POST, instance=group, prefix='slots')
        if form.is_valid() and slot_fs.is_valid():
            form.save()
            slot_fs.save()
            messages.success(request, 'Группа сохранена.')
            return redirect('backoffice:content_activities_group_edit', gpk=group.pk)
    else:
        form = ActivityGroupForm(instance=group)
        slot_fs = ScheduleSlotFormSet(instance=group, prefix='slots')

    return render_backoffice(
        request,
        'backoffice/content/activities/group_edit.html',
        active='activities',
        page_title=f'Группа · {activity.name}',
        context={
            'group': group,
            'activity': activity,
            'region': activity.region,
            'form': form,
            'slot_fs': slot_fs,
            'translation_langs': TRANSLATION_LANGS,
        },
    )


@require_POST
@backoffice_required
def content_activities_group_translate(request, gpk):
    """RU→KK/EN перевод для группы (label/teacher_name/teacher_bio)."""
    _get_group_for_user(request, gpk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    by_lang = payload.get('by_lang') or {}
    if not isinstance(by_lang, dict):
        return JsonResponse({'error': 'by_lang must be an object'}, status=400)

    result: dict[str, dict[str, str]] = {}
    for lang, values in by_lang.items():
        if lang not in {'kk', 'en'}:
            continue
        if not isinstance(values, dict):
            continue
        sanitized = {
            str(k): str(v)[:TRANSLATE_MAX_VALUE_CHARS]
            for k, v in list(values.items())[:TRANSLATE_MAX_FIELDS_PER_LANG]
            if v and str(v).strip()
        }
        if not sanitized:
            continue
        try:
            result[lang] = translate_fields(sanitized, lang)
        except TranslationConfigError as e:
            return JsonResponse({'error': str(e)}, status=503)
        except TranslationError as e:
            return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'translations': result})


@require_POST
@backoffice_required
def content_activities_group_delete(request, gpk):
    """POST: удалить группу + редирект на catalog региона (на anchor activity)."""
    group = _get_group_for_user(request, gpk)
    activity = group.activity
    label = group.label_display or f'Группа #{group.pk}'
    group.delete()
    messages.success(request, f'Группа «{label}» удалена.')
    url = reverse('backoffice:content_activities_region', kwargs={'region_pk': activity.region_id})
    return redirect(f'{url}#activity-{activity.pk}')


# ===== Content: Blog (раздел «Лента») =======================================
#
# Список постов, edit с Trix-редактором, AI-tagger через Gemini,
# отдельная taxonomy-страница для категорий и тегов. Шаблоны:
# `templates/backoffice/content/blog/`.

BLOG_POSTS_PER_PAGE = 20


def _auto_slug_for_blog(title: str) -> str:
    """SEO-friendly slug = slugify(title) + '-' + 4hex.

    4-hex суффикс (65k комбинаций) гарантирует уникальность без счётчика-цикла
    и сохраняет читаемость в URL. Пример: «Наурыз в школе» → «nauryz-v-shkole-a3f7».

    Если кто-то умудрился попасть в коллизию — повторяем до 5 раз с новой
    случайной частью; коллизия per slug — единичный шанс на десятки тысяч.
    """
    import secrets
    from django.utils.text import slugify
    base = slugify(title, allow_unicode=False) or 'post'
    base = base[:190]
    for _ in range(5):
        suffix = secrets.token_hex(2)  # 4 hex символа
        candidate = f'{base}-{suffix}'[:200]
        if not BlogPost.objects.filter(slug=candidate).exists():
            return candidate
    # Совсем не повезло — добавляем больше энтропии (8 hex).
    return f'{base}-{secrets.token_hex(4)}'[:200]


def _get_blog_post_for_user(request, pk):
    """region-scoped BlogPost или 404."""
    qs = region_scoped(
        BlogPost.objects.select_related('region', 'category').prefetch_related('tags'),
        request.user,
    )
    return get_object_or_404(qs, pk=pk)


def _blogpost_steps(post):
    """Stepper completeness для edit-страницы поста.

    Шаги:
    - Основа (RU, обязательный) — title, lead, cover_image, content
    - Перевод KZ / EN — те же translatable поля без cover
    - Публикация — is_published + published_at
    """
    def is_filled(field_name):
        val = getattr(post, field_name, '')
        if hasattr(val, 'name'):
            return bool(val and val.name)
        return bool(val and str(val).strip())

    ru_fields = [
        'title_ru',
        'lead_ru',
        'cover_image',
        'content_ru',
    ]
    kk_fields = [
        'title_kk', 'lead_kk', 'content_kk',
    ]
    en_fields = [
        'title_en', 'lead_en', 'content_en',
    ]
    seo_fields = [
        'seo_title_ru', 'seo_description_ru', 'og_title_ru', 'og_image',
    ]
    pub_fields = ['is_published', 'published_at']

    def step(id, label, fields, required=False):
        initial = {f: is_filled(f) for f in fields}
        filled = sum(1 for v in initial.values() if v)
        return {
            'id': id,
            'label': label,
            'fields': fields,
            'initial': initial,
            'filled': filled,
            'total': len(fields),
            'required': required,
        }

    return [
        step('ru', 'Основа (RU)', ru_fields, required=True),
        step('kk', 'Перевод KZ', kk_fields),
        step('en', 'Перевод EN', en_fields),
        step('seo', 'SEO', seo_fields),
        step('publish', 'Публикация', pub_fields),
    ]


def _sync_blog_post_tags(post, tags_data: list[dict]):
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


@never_cache
@backoffice_required
def content_blog_list(request):
    """Список постов с фильтрами. Region-scoped: менеджер видит свои, su — все."""
    base_qs = (
        region_scoped(BlogPost.objects.select_related('region', 'category'), request.user)
        .prefetch_related('tags')
    )

    # Не-status фильтры применяются и к counts, и к qs.
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

    # Считаем все 3 статуса по одному запросу (counts сбалансированы и не сбрасываются
    # при клике на чип — паттерн leads_list).
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

    # Для фильтра-категорий — все категории региона менеджера (или всех регионов для su)
    categories_qs = BlogCategory.objects.all().order_by('order', 'name')

    qs_dict = request.GET.copy()
    qs_dict.pop('page', None)
    base_qs_str = qs_dict.urlencode()

    # URLs для чипов status (сохраняют q/category/region, сбрасывают page).
    def _chip_url(status_value):
        params = request.GET.copy()
        params.pop('page', None)
        if status_value:
            params['status'] = status_value
        else:
            params.pop('status', None)
        encoded = params.urlencode()
        return f'?{encoded}' if encoded else '?'

    status_chips = [
        {'value': '', 'label': 'Все', 'count': status_counts['all'], 'url': _chip_url(''), 'active': is_published == ''},
        {'value': 'published', 'label': 'Опубликованные', 'count': status_counts['published'], 'url': _chip_url('published'), 'active': is_published == 'published', 'code': 'published'},
        {'value': 'draft', 'label': 'Черновики', 'count': status_counts['draft'], 'url': _chip_url('draft'), 'active': is_published == 'draft', 'code': 'draft'},
    ]

    return render_backoffice(
        request,
        'backoffice/content/blog/list.html',
        active='blog',
        page_title='Блог',
        context={
            'page': page,
            'paginator': paginator,
            'categories': categories_qs,
            'all_regions': Region.objects.filter(is_active=True) if request.user.is_superuser else None,
            'filters': {
                'status': is_published,
                'category': category_slug,
                'region': region_slug,
                'q': q,
            },
            'status_chips': status_chips,
            'base_qs': base_qs_str,
        },
    )


@never_cache
@backoffice_required
@require_http_methods(['GET', 'POST'])
def content_blog_create(request):
    """Создание поста за 1 шаг — полная форма + 2 CTA (черновик / опубликовать).

    После save редиректим на edit того же поста для дальнейших правок (паттерн
    WordPress/Ghost). slug генерируется автоматически из title.
    """
    from django.utils import timezone

    if request.method == 'POST':
        form = BlogPostEditForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            # Auto-slug — пользователю не показывается; короткий 4-hex суффикс
            # делает его глобально уникальным без counter-loop.
            title = form.cleaned_data.get('title_ru') or post.title or 'Без названия'
            post.slug = _auto_slug_for_blog(title)
            # Если is_published не пришёл (CTA «Сохранить как черновик») — False.
            # Если пришёл (CTA «Опубликовать») — True.
            post.is_published = bool(request.POST.get('publish_now'))
            if not post.published_at:
                post.published_at = timezone.now()
            post.save()
            form.save_m2m()
            _sync_blog_post_tags(post, form.cleaned_data.get('tags_json') or [])

            if post.is_published:
                messages.success(request, f'Пост «{post.title}» опубликован.')
            else:
                messages.success(request, f'Черновик «{post.title}» сохранён.')
            return redirect('backoffice:content_blog_edit', pk=post.pk)
    else:
        # Default values for new post
        form = BlogPostEditForm(
            initial={'published_at': timezone.now().strftime('%Y-%m-%dT%H:%M')},
            user=request.user,
        )

    # Все теги — глобальные, для tag-picker'а (с именами на 3 языках)
    all_tags = _tags_payload(BlogTag.objects.all())
    categories = list(BlogCategory.objects.all().order_by('order', 'name'))
    steps = _blogpost_steps_for_create()

    return render_backoffice(
        request,
        'backoffice/content/blog/create.html',
        active='blog',
        page_title='Новый пост',
        context={
            'form': form,
            'translation_langs': TRANSLATION_LANGS,
            'categories': categories,
            'all_tags_json': json.dumps(all_tags),
            'steps_json': json.dumps(steps),
            'translatable_bases_json': json.dumps(list(BLOG_POST_TRANSLATABLE)),
            'out_of_form_bases': BLOG_POST_OUT_OF_FORM_BASES,
        },
    )


def _tags_payload(qs):
    """Сериализатор тегов для `boTagPicker`. Возвращает имена на всех 3 языках,
    чтобы при смене таба (RU/KK/EN) чипы реактивно обновлялись."""
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


def _blogpost_steps_for_create():
    """Stepper для новой формы — поля пустые, шаги показывают «куда идти».
    Required только RU."""
    def step(id, label, total, required=False):
        return {
            'id': id, 'label': label, 'fields': [],
            'initial': {}, 'filled': 0, 'total': total, 'required': required,
        }
    return [
        step('ru', 'Основа (RU)', 4, required=True),
        step('kk', 'Перевод KZ', 3),
        step('en', 'Перевод EN', 3),
        step('seo', 'SEO', 4),
        step('publish', 'Публикация', 2),
    ]


@never_cache
@backoffice_required
def content_blog_edit(request, pk):
    post = _get_blog_post_for_user(request, pk)
    # ВАЖНО: ModelForm(data, instance=post) мутирует post под значения POST'а
    # (post и saved — один и тот же объект). Поэтому сохраняем оригиналы ДО
    # инициализации формы, иначе после save (commit=False) post.slug/region_id
    # будут пустыми.
    original_slug = post.slug
    original_region_id = post.region_id

    if request.method == 'POST':
        form = BlogPostEditForm(request.POST, request.FILES, instance=post, user=request.user)
        if form.is_valid():
            saved = form.save(commit=False)
            # Регион и slug на edit неизменяемы (hidden поля, могут прийти
            # пустыми). Восстанавливаем сохранённые оригиналы.
            saved.region_id = original_region_id
            if not saved.slug:
                saved.slug = original_slug
            # base поля (title/lead/content/...) — modeltranslation сам синкнет
            # из _ru, но только при save() инстанса. После save сделаем теги.
            saved.save()
            form.save_m2m()  # пусто, но на будущее
            _sync_blog_post_tags(saved, form.cleaned_data.get('tags_json') or [])
            messages.success(request, 'Пост сохранён.')
            return redirect('backoffice:content_blog_edit', pk=saved.pk)
    else:
        form = BlogPostEditForm(instance=post, user=request.user)

    steps = _blogpost_steps(post)

    # Все теги — глобальные. names на 3 языках для реактивности tag-picker.
    all_tags = _tags_payload(BlogTag.objects.all().order_by('order', 'name'))

    # Глобальные категории.
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
#
# Каждый пост может иметь одну «главную» галерею (slug='main'), которая
# рендерится на сайте после контента. Создаётся лениво — при первом upload.
# Legacy шорткоды [[gallery slug=...]] продолжают работать для других slug'ов.

BLOG_MAIN_GALLERY_SLUG = 'main'


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
    """Multi-upload в главную галерею поста. order = после последнего, шаг 10."""
    post = _get_blog_post_for_user(request, pk)
    files = request.FILES.getlist('images')
    if not files:
        return JsonResponse({'error': 'No files'}, status=400)

    gallery = _get_or_create_main_gallery(post)
    max_order = gallery.images.aggregate(Max('order'))['order__max'] or 0
    for f in files:
        max_order += 10
        BlogGalleryImage.objects.create(gallery=gallery, image=f, order=max_order)

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
    """Inline-update alt/caption translations."""
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
    """AI-генерация SEO/OG для BlogPost. Источник — title/lead/content (передаётся
    в payload, не из БД, чтобы поддержать несохранённые правки). Region-scope обязателен."""
    _get_blog_post_for_user(request, pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    content = payload.get('content') or {}
    if not isinstance(content, dict):
        return JsonResponse({'error': 'content must be an object'}, status=400)

    sanitized = {
        str(k): str(v)[:SEO_SOURCE_MAX_CHARS]
        for k, v in list(content.items())[:SEO_SOURCE_MAX_FIELDS]
        if v and str(v).strip()
    }
    if not sanitized:
        return JsonResponse(
            {'error': 'Нет исходного контента для SEO. Заполни title и lead на RU.'},
            status=400,
        )

    try:
        seo = generate_seo(sanitized)
    except TranslationConfigError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except TranslationError as e:
        return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'seo': seo})


@require_POST
@backoffice_required
def content_blog_translate(request, pk):
    """RU→KK/EN для translatable полей поста. Идентичен home_translate."""
    _get_blog_post_for_user(request, pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    by_lang = payload.get('by_lang') or {}
    if not isinstance(by_lang, dict):
        return JsonResponse({'error': 'by_lang must be an object'}, status=400)

    result: dict[str, dict[str, str]] = {}
    for lang, values in by_lang.items():
        if lang not in {'kk', 'en'}:
            continue
        if not isinstance(values, dict):
            continue
        sanitized = {
            str(k): str(v)[:TRANSLATE_MAX_VALUE_CHARS]
            for k, v in list(values.items())[:TRANSLATE_MAX_FIELDS_PER_LANG]
            if v and str(v).strip()
        }
        if not sanitized:
            continue
        try:
            result[lang] = translate_fields(sanitized, lang)
        except TranslationConfigError as e:
            return JsonResponse({'error': str(e)}, status=503)
        except TranslationError as e:
            return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'translations': result})


SUGGEST_TAGS_MAX_CONTENT = 10000


@require_POST
@backoffice_required
def content_blog_suggest_tags(request, pk):
    """POST {title, lead, content} → {tags: [{slug, name}], existing_overlap: [slug,...]}.

    Сервер не использует значения из БД (менеджер мог поменять и не сохранить).
    Список существующих тегов берётся из БД (region-scoped). Frontend
    помечает в UI пересечения как `existing` (синий чип) vs `new` (жёлтый чип).
    """
    post = _get_blog_post_for_user(request, pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    title = str(payload.get('title', ''))[:300]
    lead = str(payload.get('lead', ''))[:600]
    content = str(payload.get('content', ''))[:SUGGEST_TAGS_MAX_CONTENT]

    # Чистим HTML, чтобы Gemini не отвлекался на разметку.
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
        {
            **t,
            'is_new': t['slug'] not in existing_slug_set,
        }
        for t in suggested
    ]
    return JsonResponse({'tags': annotated})


# ----- Blog taxonomy (categories + tags) -------------------------------------


@never_cache
@backoffice_required
@require_http_methods(['GET', 'POST'])
def content_blog_taxonomy(request):
    """Одна общая страница CRUD категорий и тегов. Категории/теги ГЛОБАЛЬНЫЕ
    (одни на все регионы — см. миграцию 0006/0007). Order/slug не показываем."""
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


def _taxonomy_save(model, model_label, request, user):
    """CRUD общая логика. Глобальные категории/теги — без region.
    Order назначается автоматически (max+10 при создании, не меняется при update)."""
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
        base_slug = slugify(name_ru, allow_unicode=False) or 'tag'
        slug = base_slug[:60]
        from itertools import count
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
    _taxonomy_save(BlogCategory, 'Категория', request, request.user)
    return redirect('backoffice:content_blog_taxonomy')


@require_POST
@backoffice_required
def content_blog_tag_save(request):
    _taxonomy_save(BlogTag, 'Тег', request, request.user)
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


# ===== Content: Team (раздел «Команда») =====================================
#
# Одна модель TeamMember с фото и SEO. Region-scoped (RegionScopedAdminMixin
# pattern — менеджер видит только свой регион, su — всё). Без inline-моделей
# (TeamResumeItem удалён в team/0006).
# Шаблоны: templates/backoffice/content/team/.

TEAM_MEMBERS_PER_PAGE = 24


def _auto_slug_for_team(name: str) -> str:
    """SEO-friendly slug = slugify(name) + '-' + 4hex. Аналог _auto_slug_for_blog."""
    import secrets
    from django.utils.text import slugify
    base = slugify(name, allow_unicode=False) or 'member'
    base = base[:190]
    for _ in range(5):
        suffix = secrets.token_hex(2)
        candidate = f'{base}-{suffix}'[:200]
        if not TeamMember.objects.filter(slug=candidate).exists():
            return candidate
    return f'{base}-{secrets.token_hex(4)}'[:200]


def _get_team_member_for_user(request, pk):
    """region-scoped TeamMember или 404."""
    qs = region_scoped(
        TeamMember.objects.select_related('region'),
        request.user,
    )
    return get_object_or_404(qs, pk=pk)


def _teammember_steps(member):
    """Stepper completeness для edit-страницы."""
    def is_filled(field_name):
        val = getattr(member, field_name, '')
        if hasattr(val, 'name'):
            return bool(val and val.name)
        return bool(val and str(val).strip())

    ru_fields = ['name_ru', 'role_ru', 'photo']
    kk_fields = ['name_kk', 'role_kk']
    en_fields = ['name_en', 'role_en']
    seo_fields = ['seo_title_ru', 'seo_description_ru', 'og_title_ru', 'og_image']
    pub_fields = ['is_published', 'is_featured']

    def step(id, label, fields, required=False):
        initial = {f: is_filled(f) for f in fields}
        filled = sum(1 for v in initial.values() if v)
        return {
            'id': id,
            'label': label,
            'fields': fields,
            'initial': initial,
            'filled': filled,
            'total': len(fields),
            'required': required,
        }

    return [
        step('ru', 'Основа (RU)', ru_fields, required=True),
        step('kk', 'Перевод KZ', kk_fields),
        step('en', 'Перевод EN', en_fields),
        step('seo', 'SEO', seo_fields),
        step('publish', 'Публикация', pub_fields),
    ]


def _teammember_steps_for_create():
    def step(id, label, total, required=False):
        return {
            'id': id, 'label': label, 'fields': [],
            'initial': {}, 'filled': 0, 'total': total, 'required': required,
        }
    return [
        step('ru', 'Основа (RU)', 3, required=True),
        step('kk', 'Перевод KZ', 2),
        step('en', 'Перевод EN', 2),
        step('seo', 'SEO', 4),
        step('publish', 'Публикация', 2),
    ]


@never_cache
@backoffice_required
def content_team_list(request):
    """Карточки регионов со счётчиком членов команды (паттерн activities-list).

    Менеджер региона видит только свой регион; если регион один — сразу
    редиректит в `content_team_region`. Su видит все активные регионы и
    выбирает руками.
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
    # У менеджера ровно один регион — нет смысла показывать «карточку выбора»,
    # сразу ведём на его команду.
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
    «Программа») сверху и «Остальные» — снизу. В каждой — DnD-сортировка
    (boTeamSort), AJAX POST на content_team_reorder.
    """
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
    Order пишется как `i*10`. Group задаёт только safety-фильтр (не даём
    случайно сложить featured в non-featured список), сам флаг
    `is_featured` НЕ меняется этим эндпоинтом.
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
    """Создание члена команды за 1 шаг.
    После save редирект на edit (паттерн blog)."""
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
    # Паттерн blog: сохраняем оригиналы slug/region_id ДО init формы —
    # ModelForm мутирует instance под значения POST (см. memory
    # feedback_modelform_mutates_instance).
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
    """AI-генерация SEO/OG для TeamMember. Источник — name/role/meta/bio."""
    _get_team_member_for_user(request, pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    content = payload.get('content') or {}
    if not isinstance(content, dict):
        return JsonResponse({'error': 'content must be an object'}, status=400)

    sanitized = {
        str(k): str(v)[:SEO_SOURCE_MAX_CHARS]
        for k, v in list(content.items())[:SEO_SOURCE_MAX_FIELDS]
        if v and str(v).strip()
    }
    if not sanitized:
        return JsonResponse(
            {'error': 'Нет исходного контента для SEO. Заполни имя и должность на RU.'},
            status=400,
        )

    try:
        seo = generate_seo(sanitized)
    except TranslationConfigError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except TranslationError as e:
        return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'seo': seo})


@require_POST
@backoffice_required
def content_team_translate(request, pk):
    """RU→KK/EN для translatable полей члена команды. Идентичен home/blog translate."""
    _get_team_member_for_user(request, pk)

    try:
        payload = json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    by_lang = payload.get('by_lang') or {}
    if not isinstance(by_lang, dict):
        return JsonResponse({'error': 'by_lang must be an object'}, status=400)

    result: dict[str, dict[str, str]] = {}
    for lang, values in by_lang.items():
        if lang not in {'kk', 'en'}:
            continue
        if not isinstance(values, dict):
            continue
        sanitized = {
            str(k): str(v)[:TRANSLATE_MAX_VALUE_CHARS]
            for k, v in list(values.items())[:TRANSLATE_MAX_FIELDS_PER_LANG]
            if v and str(v).strip()
        }
        if not sanitized:
            continue
        try:
            result[lang] = translate_fields(sanitized, lang)
        except TranslationConfigError as e:
            return JsonResponse({'error': str(e)}, status=503)
        except TranslationError as e:
            return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'translations': result})
