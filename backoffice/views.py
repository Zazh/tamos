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
    translate_fields,
)
from feedback.models import Lead
from pages.models import ContactsPage, HomeGalleryImage, HomePage
from programs.models import ProgramPage
from regions.models import Region

from .forms import (
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
    TRANSLATION_LANGS,
    HOME_TRANSLATABLE,
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


# ----- content: ProgramPage --------------------------------------------------


@never_cache
@backoffice_required
def content_program_list(request):
    qs = (
        region_scoped(ProgramPage.objects.select_related('region'), request.user)
        .annotate(
            audience_count=Count('audience_items', distinct=True),
            variant_count=Count('variant_cards', distinct=True),
            team_count=Count('team_members', distinct=True),
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
