"""Gemini-based авто-перевод CMS-полей для backoffice.

Один REST-вызов на пачку полей (1 целевой язык за раз). Используется
`generativelanguage.googleapis.com` с `responseMimeType=application/json` —
модель сама возвращает валидный JSON, парсим без выкрутасов.

Ключ читается из settings.GEMINI_API_KEY. Если ключ пустой — функция
кидает `TranslationConfigError` (backoffice view конвертит в 503).
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


class TranslationError(Exception):
    """Базовая ошибка перевода — для всех ретраябл/нет ситуаций."""


class TranslationConfigError(TranslationError):
    """Ключ не настроен или модель недоступна — config-level."""


_LANG_NAMES = {
    'kk': 'казахский',
    'en': 'английский',
    'ru': 'русский',
}

# Краткое позиционирование школы — source of truth: tamos/memory/positioning.md.
# Подмешивается в SEO-prompt'ы как контекст бренда (полное название, ниша, тон).
# При смене позиционирования синхронизируй этот блок с positioning.md.
SCHOOL_CONTEXT = (
    'Space School — международная частная школа в Астане и Актау с '
    'физико-математическим уклоном и космической тематикой, аккредитованная '
    'Cambridge International Education. Программа Cambridge от Primary до A-Level, '
    'двойной аттестат (казахстанский + Cambridge), выпускники поступают как в '
    'NU и другие казахстанские вузы, так и в зарубежные (через SAT). '
    'Полное брендовое название — «Space School», латиницей, не сокращать.'
)

_PROMPT_TEMPLATE = """Ты — переводчик для CMS международной школы Space School (для детей, родителей, маркетинг).
Переведи значения полей с русского на {target_name}.

Правила:
1. Сохрани HTML-теги в точности (например <span class="hero-fit">, <strong>, <br>). Переводи только текст между тегами.
2. Сохрани все CSS-классы и атрибуты внутри тегов (class="hero-fit", class="text-gold" и т.п.) — НЕ переводи их.
3. Сохрани переносы строк \\n — они смысловые.
4. Тон: дружелюбный, для родителей школьников. Без машинного канцелярита.
5. Длина перевода — близко к оригиналу (±20%); это UI-копия, важно не «растечься».
6. Не добавляй пояснений, кавычек или markdown — только перевод.

Верни строго JSON-объект, где ключи совпадают с input один-в-один, значения — переведённые строки.

INPUT (JSON):
{payload}
"""


# Коды ошибок, при которых имеет смысл fallback на следующую модель.
# 401/403 не повторяем — там проблема с ключом / биллингом, fallback не поможет.
# 400 не повторяем — это плохой payload (наш JSON), у всех моделей один результат.
_RETRYABLE_HTTP_CODES = {404, 408, 409, 429, 500, 502, 503, 504}


def _try_one_model(model: str, prompt: str, api_key: str, timeout: float) -> str:
    """Один POST-вызов к конкретной модели. Не делает fallback.

    Поднимает:
    - `TranslationConfigError` (401/403) — фатально, fallback не поможет.
    - `_RetryableModelError` (404/429/5xx/parse error) — caller перейдёт к
      следующей модели в списке.
    - `TranslationError` (400, URLError, прочее) — фатально, не ретраим.
    """
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'

    body = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.2,
            'responseMimeType': 'application/json',
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        detail = ''
        try:
            detail = e.read().decode('utf-8', errors='replace')[:400]
        except Exception:
            pass
        logger.warning('Gemini[%s] HTTPError %s: %s', model, e.code, detail)
        if e.code in (401, 403):
            raise TranslationConfigError(
                f'Gemini вернул {e.code} — проверь API_GEMINI_KEY и доступ к модели {model}.'
            ) from e
        if e.code in _RETRYABLE_HTTP_CODES:
            raise _RetryableModelError(f'Gemini[{model}] HTTP {e.code}: {detail[:200]}') from e
        raise TranslationError(f'Gemini[{model}] HTTP {e.code}: {detail[:200]}') from e
    except urllib.error.URLError as e:
        # Network-level (timeout, DNS) — пробуем следующую модель (может endpoint этой
        # пингуется хуже из-за региона). Если все падают — последняя ошибка пробросится.
        raise _RetryableModelError(f'Gemini[{model}] не достучались: {e.reason}') from e

    try:
        parsed = json.loads(raw)
    except ValueError as e:
        raise _RetryableModelError(f'Gemini[{model}] невалидный JSON: {raw[:200]}') from e

    try:
        return parsed['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError, TypeError) as e:
        finish = parsed.get('candidates', [{}])[0].get('finishReason') if isinstance(parsed, dict) else None
        raise _RetryableModelError(
            f'Gemini[{model}] не нашёл текст (finishReason={finish}). Сырое: {raw[:200]}'
        ) from e


class _RetryableModelError(TranslationError):
    """Внутренняя метка: caller может перейти к следующей модели в fallback chain."""


def _call_gemini(prompt: str, *, timeout: float = 30.0) -> str:
    """Высокоуровневый вызов с fallback по списку моделей из settings.

    Пробегается по `settings.GEMINI_MODELS` в порядке приоритета. Первая
    успешная модель возвращает ответ. На retryable-ошибках (404/429/5xx/
    невалидный JSON/network) → переходит к следующей модели. Конфиг-ошибки
    (401/403) и плохой payload (400) — мгновенно фатальны (fallback не поможет).
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '') or ''
    if not api_key:
        raise TranslationConfigError(
            'GEMINI_API_KEY не задан в .env. Добавь API_GEMINI_KEY=... и перезапусти контейнер.'
        )

    models = list(getattr(settings, 'GEMINI_MODELS', None) or ['gemini-2.5-flash'])
    if not models:
        raise TranslationConfigError('GEMINI_MODELS пуст — задай хотя бы одну модель в .env.')

    last_error: TranslationError | None = None
    for i, model in enumerate(models):
        try:
            text = _try_one_model(model, prompt, api_key, timeout)
            if i > 0:
                logger.info('Gemini fallback сработал: %s (после %d неудач)', model, i)
            return text
        except _RetryableModelError as e:
            last_error = e
            continue  # пробуем следующую модель

    # Все модели исчерпаны — кидаем последнюю ошибку как обычный TranslationError
    raise TranslationError(
        f'Все {len(models)} Gemini-модели не ответили. Последняя ошибка: {last_error}'
    ) from last_error


def translate_fields(values: dict[str, str], target_lang: str, *, timeout: float = 30.0) -> dict[str, str]:
    """Перевести dict ru-значений на `target_lang`.

    Args:
        values: {field_name: ru_text}. Пустые/None значения пропускаются.
        target_lang: 'kk' или 'en'.
        timeout: секунд на ответ Gemini.

    Returns:
        {field_name: translated_text} — тот же набор ключей, что во вход.
        Поля, которые модель не вернула — выпадут (но в норме не должны).

    Raises:
        TranslationConfigError: ключ пуст / 401/403 от API.
        TranslationError: всё остальное (network, 5xx, невалидный JSON).
    """
    if target_lang not in _LANG_NAMES or target_lang == 'ru':
        raise TranslationError(f'Неподдерживаемый target_lang: {target_lang!r}')

    cleaned = {k: v for k, v in values.items() if v and str(v).strip()}
    if not cleaned:
        return {}

    prompt = _PROMPT_TEMPLATE.format(
        target_name=_LANG_NAMES[target_lang],
        payload=json.dumps(cleaned, ensure_ascii=False, indent=2),
    )
    text = _call_gemini(prompt, timeout=timeout)

    try:
        translated = json.loads(text)
    except ValueError as e:
        raise TranslationError(f'Модель вернула не-JSON: {text[:200]}') from e

    if not isinstance(translated, dict):
        raise TranslationError(f'Модель вернула не-объект: {text[:200]}')

    return {k: str(v) for k, v in translated.items() if k in cleaned}


_SEO_PROMPT_TEMPLATE = """Ты — SEO-копирайтер для сайта международной школы Space School.

Контекст бренда:
{school_context}

На входе — контент главной страницы региона (в т.ч. с HTML-тегами; игнорируй разметку, бери смысл текста). Сгенерируй SEO/OG поля для трёх языков: русский (ru), казахский (kk), английский (en).

Поля на каждый язык:
- "seo_title" — заголовок <title>. До 60 символов. Должен содержать «Space School» (или локализованный аналог: на kk — «Space School», на en — «Space School») и ключевую суть страницы.
- "seo_description" — meta description. До 160 символов. Чёткое описание ценности для родителя, без воды, без «лучшая школа в мире» клише.
- "og_title" — для соцсетей (Facebook/LinkedIn/Telegram). До 70 символов. Эмоциональнее чем seo_title.
- "og_description" — описание для шеринга. До 200 символов. Чуть свободнее тоном, чем seo_description.

Правила:
1. Без markdown, без кавычек вокруг текста, без эмодзи.
2. На казахском и английском — нативные формулировки, не калька с RU.
3. Тон — для родителя школьника: спокойный, доверительный, без хайпа.
4. Уважай лимиты длины — это hard cap для UI.

Контент страницы (RU):
{payload}

Верни строго JSON-объект в формате:
{{
  "ru": {{"seo_title": "...", "seo_description": "...", "og_title": "...", "og_description": "..."}},
  "kk": {{"seo_title": "...", "seo_description": "...", "og_title": "...", "og_description": "..."}},
  "en": {{"seo_title": "...", "seo_description": "...", "og_title": "...", "og_description": "..."}}
}}
Без обёрток, без дополнительных ключей."""


SEO_OUTPUT_FIELDS = ('seo_title', 'seo_description', 'og_title', 'og_description')
SEO_OUTPUT_LANGS = ('ru', 'kk', 'en')


_TAGS_PROMPT_TEMPLATE = """Ты — SEO-стратег и редактор блога международной школы Space School.

Контекст бренда:
{school_context}

Задача: предложи 4–7 SEO-friendly и UX-friendly тегов для статьи блога.

Правила:
1. Каждый тег — 1–3 слова на РУССКОМ. Без хэштега, без знаков препинания, без эмодзи.
2. Должны быть осмысленные «общие» темы (то, что родители ищут): «Cambridge», «Олимпиады», «Робототехника», «Стажировка MIT», «STEM», «Подготовка к школе», «Жизнь школы», и т.п. НЕ выдавай имена людей, конкретные даты, числа, города как теги.
3. ПЕРЕИСПОЛЬЗУЙ существующие теги если они подходят. Подходящий = семантически совпадает (даже если слова чуть другие — выбирай тег из списка).
4. Slug — латинский kebab-case (mit-internship, cambridge-exams). Для существующих тегов — бери slug из списка, ничего не меняй.
5. Возвращай порядок «от самого важного к менее важному» — первые 2–3 тега должны быть наиболее релевантны теме.

Уже существующие теги в этом регионе (формат "slug — Название"):
{existing}

Контент статьи:
title: {title}
lead: {lead}
content: {content}

Верни строго JSON-массив объектов, без обёрток:
[{{"slug": "mit-internship", "name": "Стажировка MIT"}}, ...]

Где slug — латиница kebab-case, name — Русское Название (как читается в UI)."""


TAGS_MIN_COUNT = 3
TAGS_MAX_COUNT = 8


def suggest_tags(
    *,
    title: str,
    lead: str,
    content: str,
    existing_tags: list[dict] | None = None,
    timeout: float = 30.0,
) -> list[dict]:
    """Предложить теги для статьи блога через Gemini.

    Args:
        title, lead, content: текст статьи на RU. content уже без HTML
            (вызывающая сторона должна strip_tags).
        existing_tags: [{'slug': ..., 'name': ...}] — уже существующие
            теги региона. Модель будет переиспользовать подходящие.

    Returns:
        Список dict'ов `{'slug': ..., 'name': ...}` длиной 3–8.

    Raises:
        TranslationConfigError / TranslationError — см. _call_gemini.
    """
    title = (title or '').strip()
    lead = (lead or '').strip()
    content = (content or '').strip()
    if not title and not lead and not content:
        return []

    existing = existing_tags or []
    if existing:
        existing_lines = '\n'.join(
            f"- {t.get('slug', '')} — {t.get('name', '')}"
            for t in existing if t.get('slug') and t.get('name')
        )
    else:
        existing_lines = '(нет — все теги будут новыми)'

    prompt = _TAGS_PROMPT_TEMPLATE.format(
        school_context=SCHOOL_CONTEXT,
        existing=existing_lines,
        title=title[:300],
        lead=lead[:600],
        content=content[:6000],
    )
    text = _call_gemini(prompt, timeout=timeout)

    try:
        parsed = json.loads(text)
    except ValueError as e:
        raise TranslationError(f'Модель вернула не-JSON: {text[:200]}') from e

    if not isinstance(parsed, list):
        raise TranslationError(f'Модель вернула не-массив: {text[:200]}')

    cleaned: list[dict] = []
    seen_slugs: set[str] = set()
    for item in parsed[:TAGS_MAX_COUNT]:
        if not isinstance(item, dict):
            continue
        slug = str(item.get('slug', '')).strip().lower()
        name = str(item.get('name', '')).strip()
        if not slug or not name or slug in seen_slugs:
            continue
        # Жёсткая нормализация slug — латиница/цифры/дефис, до 64 chars.
        safe_slug = ''.join(c for c in slug if c.isalnum() or c == '-')[:64].strip('-')
        if not safe_slug:
            continue
        seen_slugs.add(safe_slug)
        cleaned.append({'slug': safe_slug, 'name': name[:80]})

    return cleaned


def generate_seo(content: dict[str, str], *, timeout: float = 45.0) -> dict[str, dict[str, str]]:
    """Сгенерировать SEO/OG поля на основе контента страницы.

    Args:
        content: {field_name: text} на русском (источник правды).
                 Хорошие источники: hero_title, hero_subtitle, about_title, about_body.
                 HTML внутри значений допустим — Gemini игнорирует разметку.
        timeout: секунд на ответ.

    Returns:
        {lang: {seo_field: text}} для языков из SEO_OUTPUT_LANGS.

    Raises:
        TranslationConfigError / TranslationError — см. _call_gemini.
    """
    cleaned = {k: str(v) for k, v in content.items() if v and str(v).strip()}
    if not cleaned:
        return {}

    prompt = _SEO_PROMPT_TEMPLATE.format(
        school_context=SCHOOL_CONTEXT,
        payload=json.dumps(cleaned, ensure_ascii=False, indent=2),
    )
    text = _call_gemini(prompt, timeout=timeout)

    try:
        parsed = json.loads(text)
    except ValueError as e:
        raise TranslationError(f'Модель вернула не-JSON: {text[:200]}') from e

    if not isinstance(parsed, dict):
        raise TranslationError(f'Модель вернула не-объект: {text[:200]}')

    result: dict[str, dict[str, str]] = {}
    for lang in SEO_OUTPUT_LANGS:
        per_lang = parsed.get(lang)
        if not isinstance(per_lang, dict):
            continue
        result[lang] = {
            field: str(per_lang[field])
            for field in SEO_OUTPUT_FIELDS
            if field in per_lang and per_lang[field]
        }
    return result
