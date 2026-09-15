"""Дозаполняет ПУСТЫЕ `_kk`/`_en` у translatable-полей через Gemini.

Запуск:
    docker compose exec -T tamosapp python manage.py shell < scripts/backfill_translations.py

Сухой прогон (ничего не пишет, только список того, что будет переведено):
    docker compose exec -T -e BACKFILL_DRY_RUN=1 tamosapp python manage.py shell < scripts/backfill_translations.py

Правила
-------
* Пишем ТОЛЬКО в пустые целевые поля. Непустое `_kk`/`_en` — это либо ручной
  перевод менеджера, либо уже прогнанный авто-перевод; не трогаем никогда.
* Источник — `_ru`. Если он пуст, поле пропускается (переводить нечего).
* Идемпотентно: повторный запуск подхватит только то, что осталось пустым
  (например после сбоя сети на середине).
* Пачки формируются по бюджету символов, а не по количеству полей — длинный
  HTML-контент не должен ехать в одном запросе с двумя десятками alt-текстов.
* Ошибка одной пачки не роняет прогон: пачка пропускается, остальные едут
  дальше, сводка по сбоям печатается в конце.
"""
import os
import time

from django.db import transaction
from modeltranslation.translator import translator

from core.gemini_translate import TranslationError, translate_fields

TARGET_LANGS = ('kk', 'en')
CHUNK_CHAR_BUDGET = 6000   # суммарно символов ru-текста в одном запросе
CHUNK_MAX_FIELDS = 12
SLEEP_BETWEEN_CHUNKS = 1.5  # сек, чтобы не упереться в rate-limit

DRY_RUN = bool(os.environ.get('BACKFILL_DRY_RUN'))


def collect_jobs(lang):
    """[(obj, base_field, ru_text)] — всё, что пусто на `lang` и непусто на ru."""
    jobs = []
    for model in sorted(translator.get_registered_models(), key=lambda m: m._meta.label):
        opts = translator.get_options_for_model(model)
        bases = sorted(set(opts.fields))
        for obj in model.objects.all():
            for base in bases:
                ru = getattr(obj, f'{base}_ru', None)
                target = getattr(obj, f'{base}_{lang}', None)
                if ru and str(ru).strip() and not (target and str(target).strip()):
                    jobs.append((obj, base, str(ru)))
    return jobs


def chunked(jobs):
    """Нарезать задания на пачки по бюджету символов."""
    batch, size = [], 0
    for job in jobs:
        text_len = len(job[2])
        if batch and (size + text_len > CHUNK_CHAR_BUDGET or len(batch) >= CHUNK_MAX_FIELDS):
            yield batch
            batch, size = [], 0
        batch.append(job)
        size += text_len
    if batch:
        yield batch


def run():
    total_written, failures = 0, []

    for lang in TARGET_LANGS:
        jobs = collect_jobs(lang)
        print(f'\n===== {lang.upper()}: полей к переводу — {len(jobs)} =====')
        if not jobs:
            continue

        batches = list(chunked(jobs))
        for i, batch in enumerate(batches, 1):
            # Ключи делаем опаковыми: имена полей повторяются между объектами.
            payload = {f'k{n}': ru for n, (_, _, ru) in enumerate(batch)}
            label = f'[{lang} {i}/{len(batches)}] {len(batch)} полей, {sum(len(v) for v in payload.values())} симв.'

            if DRY_RUN:
                print(f'{label} — DRY RUN')
                for n, (obj, base, ru) in enumerate(batch):
                    print(f'    {obj._meta.label}#{obj.pk}.{base}: {ru[:60]!r}')
                continue

            try:
                result = translate_fields(payload, lang)
            except TranslationError as e:
                print(f'{label} — ОШИБКА: {e}')
                failures.append((lang, i, str(e)))
                continue

            written = 0
            with transaction.atomic():
                for n, (obj, base, _) in enumerate(batch):
                    value = result.get(f'k{n}')
                    if not value or not value.strip():
                        continue
                    attr = f'{base}_{lang}'
                    # Перечитываем из БД: между сбором и записью поле мог
                    # заполнить менеджер через backoffice.
                    fresh = type(obj).objects.filter(pk=obj.pk).values_list(attr, flat=True).first()
                    if fresh and str(fresh).strip():
                        continue
                    setattr(obj, attr, value.strip())
                    obj.save(update_fields=[attr])
                    written += 1

            total_written += written
            print(f'{label} — записано {written}')
            time.sleep(SLEEP_BETWEEN_CHUNKS)

    print(f'\n===== ИТОГО записано полей: {total_written} =====')
    if failures:
        print(f'Пачек с ошибкой: {len(failures)}')
        for lang, i, err in failures:
            print(f'  {lang} #{i}: {err[:140]}')
        print('Прогон идемпотентен — просто запусти скрипт ещё раз.')


run()
