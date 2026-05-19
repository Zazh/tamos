"""Переводит пустые msgstr в .po через core.gemini_translate.

Запуск: `docker compose exec tamosapp python manage.py shell <
scripts/translate_po.py`

Логика:
- Для каждого языка (kk, en) собирает все entries с пустым msgstr.
- Пакетами по BATCH_SIZE отправляет в Gemini (translate_fields).
- Заполняет msgstr и периодически сохраняет .po.
- Plural-формы (msgid_plural) обрабатывает отдельно: переводит singular и plural,
  раскладывает по slot'ам через nplurals (для kk и en nplurals=2: 0=one, 1=other).
"""
import time

import polib

from core.gemini_translate import (
    TranslationError,
    translate_fields,
)


LANGS = ['kk', 'en']
BATCH_SIZE = 15
SLEEP_BETWEEN_BATCHES = 2.0  # сек, чтобы не упереться в rate-limit


def _translate_batch(msgids: list[str], lang: str) -> dict[str, str]:
    """Один пакетный вызов Gemini. Возвращает {msgid: translated}."""
    values = {f'k{i}': m for i, m in enumerate(msgids)}
    out = translate_fields(values, lang)
    return {msgids[int(k[1:])]: v for k, v in out.items() if k.startswith('k')}


def _translate_singular(po, lang: str) -> int:
    entries = [
        e for e in po
        if not e.msgid_plural and not e.msgstr and not e.obsolete and e.msgid
    ]
    print(f'  singular: {len(entries)} to translate')
    translated_count = 0
    for i in range(0, len(entries), BATCH_SIZE):
        batch = entries[i:i + BATCH_SIZE]
        msgids = [e.msgid for e in batch]
        try:
            mapping = _translate_batch(msgids, lang)
        except TranslationError as exc:
            print(f'    batch {i}: ERROR {exc}')
            continue
        for e in batch:
            v = mapping.get(e.msgid)
            if v:
                e.msgstr = v
                translated_count += 1
        po.save()  # промежуточный save после каждого пакета
        print(f'    batch {i // BATCH_SIZE + 1}/{(len(entries) + BATCH_SIZE - 1) // BATCH_SIZE}: '
              f'+{sum(1 for e in batch if e.msgstr)} translated')
        time.sleep(SLEEP_BETWEEN_BATCHES)
    return translated_count


def _translate_plurals(po, lang: str) -> int:
    """Переводит singular+plural msgid'ы. У kk и en nplurals=2 (one/other)."""
    entries = [
        e for e in po
        if e.msgid_plural and not e.obsolete and (
            not e.msgstr_plural.get(0) or not e.msgstr_plural.get(1)
        )
    ]
    print(f'  plural: {len(entries)} entries to translate')
    translated_count = 0
    for e in entries:
        try:
            sing_map = _translate_batch([e.msgid], lang)
            plur_map = _translate_batch([e.msgid_plural], lang)
        except TranslationError as exc:
            print(f'    plural {e.msgid!r}: ERROR {exc}')
            continue
        sing = sing_map.get(e.msgid, '')
        plur = plur_map.get(e.msgid_plural, '')
        if sing:
            e.msgstr_plural[0] = sing
        if plur:
            e.msgstr_plural[1] = plur
        if sing or plur:
            translated_count += 1
        time.sleep(SLEEP_BETWEEN_BATCHES / 2)
    po.save()
    return translated_count


def main():
    for lang in LANGS:
        path = f'/app/locale/{lang}/LC_MESSAGES/django.po'
        print(f'== {lang} ({path}) ==')
        po = polib.pofile(path)
        n_sing = _translate_singular(po, lang)
        n_plur = _translate_plurals(po, lang)
        po.save()
        print(f'  done: singular +{n_sing}, plural +{n_plur}')


main()
