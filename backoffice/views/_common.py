"""Общие хелперы для backoffice-views.

Извлечены повторяющиеся паттерны из per-section views:
  * AI-перевод (`run_translate`) и AI-SEO (`run_seo`) — практически идентичные
    тела повторялись 8 и 6 раз соответственно.
  * Slug auto-gen (`auto_slug`) — повторялся 4 раза с разными моделями.
  * Region-scoped get-helpers — `get_for_user_or_404`.
  * Galleries (`serialize_image`, `gallery_upload`/`reorder`/`update`/`delete`)
    — для inline-галерей home/blog/events.
  * Stepper builder (`make_stepper`) — общая фабрика для completeness-шагов.
  * Status chips (`make_status_chips`) — для blog/events/flatpages/gallery list.
"""

import json
import secrets

from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from core.gemini_translate import (
    TranslationConfigError,
    TranslationError,
    generate_seo,
    translate_fields,
)
from ..shortcuts import region_scoped


# Защита от мусорных payload'ов и слишком длинных значений.
TRANSLATE_MAX_FIELDS_PER_LANG = 30
TRANSLATE_MAX_VALUE_CHARS = 5000
SEO_SOURCE_MAX_FIELDS = 12
SEO_SOURCE_MAX_CHARS = 8000

# Какие языки переводим (RU — источник, KK/EN — цели).
TRANSLATE_TARGET_LANGS = frozenset({'kk', 'en'})


def parse_json_body(request):
    """Парсит JSON-тело запроса; на ошибку возвращает `(None, JsonResponse 400)`.

    Использование:
        data, err = parse_json_body(request)
        if err: return err
        ...
    """
    try:
        return json.loads(request.body or '{}'), None
    except (ValueError, TypeError):
        return None, JsonResponse({'error': 'Invalid JSON'}, status=400)


def run_translate(request):
    """Полное тело translate-view: парсит `{by_lang: {kk/en: {field: ru_text}}}`,
    переводит через Gemini, возвращает `JsonResponse({translations: {...}})`.

    Сервер не пишет в БД — возвращает переведённые значения, клиент заполняет
    инпуты, менеджер смотрит и сабмитит общую форму сам.

    Используется идентично во всех translate-endpoint'ах. Region-scope проверяет
    сама view (вызывает `_get_*_for_user` для 404), затем передаёт request сюда.
    """
    payload, err = parse_json_body(request)
    if err:
        return err

    by_lang = payload.get('by_lang') or {}
    if not isinstance(by_lang, dict):
        return JsonResponse({'error': 'by_lang must be an object'}, status=400)

    result: dict[str, dict[str, str]] = {}
    for lang, values in by_lang.items():
        if lang not in TRANSLATE_TARGET_LANGS:
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


def run_seo(request, empty_hint):
    """Полное тело SEO-view: парсит `{content: {field: ru_text}}`, генерирует
    SEO/OG через Gemini, возвращает `JsonResponse({seo: {lang: {field: text}}})`.

    Args:
        empty_hint: текст ошибки если payload пустой
            (например `'Заполни title и lead на RU.'`).
    """
    payload, err = parse_json_body(request)
    if err:
        return err

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
            {'error': f'Нет исходного контента для SEO. {empty_hint}'},
            status=400,
        )

    try:
        seo = generate_seo(sanitized)
    except TranslationConfigError as e:
        return JsonResponse({'error': str(e)}, status=503)
    except TranslationError as e:
        return JsonResponse({'error': str(e)}, status=502)

    return JsonResponse({'seo': seo})


def auto_slug(title, *, model, prefix='post', slug_field='slug', max_length=200):
    """SEO-friendly slug = `slugify(title) + '-' + 4hex`.

    4-hex суффикс (65k комбинаций) гарантирует уникальность без счётчика-цикла
    и сохраняет читаемость в URL. Пример: «Наурыз в школе» → «nauryz-v-shkole-a3f7».

    Если случилась коллизия — повторяем до 5 раз с новой случайной частью.
    На совсем редкий случай — fallback с 8-hex суффиксом.

    Args:
        model: класс модели для проверки uniqueness (`BlogPost`, `Event`, `Album`,
          `TeamMember`).
        prefix: дефолтный slug-prefix если slugify(title) дал пусто
          (часто 'post' / 'event' / 'album' / 'member').
        slug_field: имя поля slug в модели (для редких случаев когда не slug).
        max_length: максимум для slug'а на уровне БД.
    """
    base = slugify(title, allow_unicode=False) or prefix
    base = base[:max_length - 10]  # резерв под -XXXX и -XXXXXXXX
    for _ in range(5):
        suffix = secrets.token_hex(2)
        candidate = f'{base}-{suffix}'[:max_length]
        if not model.objects.filter(**{slug_field: candidate}).exists():
            return candidate
    return f'{base}-{secrets.token_hex(4)}'[:max_length]


def get_for_user_or_404(qs, request, pk, *, region_field='region'):
    """Region-scoped queryset + get_object_or_404. Менеджер видит только свой
    регион, superuser — всё; staff без региона — none → 404.
    """
    scoped = region_scoped(qs, request.user, region_field=region_field)
    return get_object_or_404(scoped, pk=pk)


# ----- Stepper completeness -------------------------------------------------


def make_step(obj, *, id, label, fields, required=False):
    """Один шаг completeness-stepper'а.

    `filled` считается по объекту (`obj`): для FileField — по наличию `.name`,
    для остальных — по непустому stripped значению. Frontend (Alpine
    `boFormSteps`) пересчитывает `filled` на лету по input-событиям.
    """
    def is_filled(field_name):
        val = getattr(obj, field_name, '')
        if hasattr(val, 'name'):
            return bool(val and val.name)
        return bool(val and str(val).strip())

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


def make_readonly_step(*, id, label, filled, total):
    """Информационный шаг для inline-секций (read-only, JS не отслеживает изменения)."""
    return {
        'id': id,
        'label': label,
        'fields': [],
        'initial': {},
        'filled': filled,
        'total': total or 1,
        'required': False,
        'readonly': True,
    }


def make_blank_step(*, id, label, total, required=False):
    """Пустой шаг для create-формы (объекта ещё нет → filled=0). Показывает
    «куда идти» в stepper'е."""
    return {
        'id': id, 'label': label, 'fields': [],
        'initial': {}, 'filled': 0, 'total': total, 'required': required,
    }


# ----- Status chips (для list-страниц с фильтром по is_published) ------------


def make_chip_url(request, *, status_value, status_key='status'):
    """Линк для статус-чипа, сохраняющий остальные GET-параметры (q/category/region).

    Сбрасывает `page` — иначе после фильтра остаётся «странная» page=2 при пустом
    результате на 2-й странице.
    """
    params = request.GET.copy()
    params.pop('page', None)
    if status_value:
        params[status_key] = status_value
    else:
        params.pop(status_key, None)
    encoded = params.urlencode()
    return f'?{encoded}' if encoded else '?'


def make_published_chips(request, *, counts, active):
    """Стандартный набор «Все / Опубликованные / Черновики» для blog/events/
    flatpages/gallery list."""
    return [
        {
            'value': '', 'label': 'Все', 'count': counts['all'],
            'url': make_chip_url(request, status_value=''),
            'active': active == '',
        },
        {
            'value': 'published', 'label': 'Опубликованные',
            'count': counts['published'],
            'url': make_chip_url(request, status_value='published'),
            'active': active == 'published',
            'code': 'published',
        },
        {
            'value': 'draft', 'label': 'Черновики',
            'count': counts['draft'],
            'url': make_chip_url(request, status_value='draft'),
            'active': active == 'draft',
            'code': 'draft',
        },
    ]


# ----- Inline-галерея (home/blog/events) ------------------------------------


def serialize_gallery_image(img, *, locale_bases=('alt', 'caption')):
    """JSON-представление одной картинки галереи для frontend Alpine-компонента.

    Возвращает базовые поля (pk, url, order) + развёрнутые `_ru/_kk/_en`
    значения для каждого base в `locale_bases`.

    `url` берётся из `img.image.url`. Если у модели есть `image_compressed`
    с try/except — используется как thumb_url (нужно для album-gallery).
    """
    out = {
        'pk': img.pk,
        'url': img.image.url if img.image else '',
        'order': getattr(img, 'order', 0),
    }
    for base in locale_bases:
        for lang in ('ru', 'kk', 'en'):
            out[f'{base}_{lang}'] = getattr(img, f'{base}_{lang}', '') or ''
    return out


def update_gallery_image_translations(img, payload, *, fields):
    """Inline-update alt/caption translations. Возвращает True если что-то поменялось.

    Args:
      fields: имена _ru/_kk/_en полей для обновления (например
        `('alt_ru', 'alt_kk', 'alt_en', 'caption_ru', 'caption_kk', 'caption_en')`).
    """
    bases = set()
    for field in fields:
        if field in payload:
            setattr(img, field, str(payload[field])[:300])
            # из 'alt_ru' → 'alt'
            for lang in ('_ru', '_kk', '_en'):
                if field.endswith(lang):
                    bases.add(field[:-len(lang)])
                    break

    # Синкаем base-поле из _ru (modeltranslation требует не-пустую base).
    for base in bases:
        setattr(img, base, getattr(img, f'{base}_ru', '') or getattr(img, base, '') or '')

    update_fields = list(fields) + list(bases)
    img.save(update_fields=update_fields)


def append_to_gallery(gallery_qs_or_manager, files, *, model, extra_kwargs=None, order_step=10):
    """Создаёт новые `GalleryImage`-подобные объекты в конце галереи.

    Возвращает list of created instances в порядке создания.

    Args:
      gallery_qs_or_manager: related manager (`gallery.images`).
      files: list of UploadedFile.
      model: класс GalleryImage-подобной модели.
      extra_kwargs: dict добавочных kwargs на create (например `{'gallery': obj}`).
    """
    max_order = gallery_qs_or_manager.aggregate(Max('order'))['order__max'] or 0
    created = []
    kwargs = dict(extra_kwargs or {})
    for f in files:
        max_order += order_step
        img = model.objects.create(image=f, order=max_order, **kwargs)
        created.append(img)
    return created


def apply_safe_reorder(model, *, queryset, order_payload, order_step=10):
    """Применяет DnD-порядок безопасно: фильтрует pk через own_ids чтобы менеджер
    не мог пересортировать чужие записи."""
    own_ids = set(queryset.values_list('pk', flat=True))
    safe_order = [int(p) for p in order_payload if int(p) in own_ids]
    for i, pk in enumerate(safe_order):
        model.objects.filter(pk=pk).update(order=i * order_step)
