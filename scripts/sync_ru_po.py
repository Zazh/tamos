"""Проставляет `msgstr = msgid` во всех записях `locale/ru/LC_MESSAGES/django.po`.

Запуск (после каждого `makemessages -l ru`):
    docker compose exec tamosapp python scripts/sync_ru_po.py

Зачем нужен идентичный ru-каталог
---------------------------------
Русский — исходный язык всех msgid, «переводить» его не надо. Но каталог
обязан существовать и быть ЗАПОЛНЕННЫМ:

`settings.LANGUAGE_CODE = 'kk'` (гос-язык по compliance), а Django для любого
языка, отличного от LANGUAGE_CODE, подмешивает каталог LANGUAGE_CODE как
fallback (`DjangoTranslation._add_fallback`). Без заполненного ru-каталога
каждая `{% trans %}`-строка на русских страницах отдавала КАЗАХСКИЙ текст.

Пустой msgstr не спасает: `msgfmt` выбрасывает такие записи из .mo, и gettext
снова уходит в kk-fallback. Поэтому msgstr должен быть равен msgid физически.

Без внешних зависимостей (polib в образе нет) — .po парсится построчно.
"""
import json
import pathlib
import sys

PO_PATH = (
    pathlib.Path(__file__).resolve().parent.parent
    / 'locale' / 'ru' / 'LC_MESSAGES' / 'django.po'
)


def _read_multiline(lines, i, keyword):
    """Собрать значение msgid/msgstr (учитывая продолжения в кавычках)."""
    parts = [lines[i][len(keyword) + 1:]]
    i += 1
    while i < len(lines) and lines[i].startswith('"'):
        parts.append(lines[i])
        i += 1
    return ''.join(json.loads(p) for p in parts), i


def _quote(value):
    return json.dumps(value, ensure_ascii=False)


def main() -> int:
    if not PO_PATH.exists():
        print(f'Нет файла {PO_PATH}. Сначала: manage.py makemessages -l ru', file=sys.stderr)
        return 1

    blocks = PO_PATH.read_text(encoding='utf-8').split('\n\n')
    filled = 0

    for bi, block in enumerate(blocks):
        lines = block.split('\n')
        if not any(l.startswith('msgid ') for l in lines):
            continue

        out, i, msgid, touched = [], 0, None, False
        while i < len(lines):
            line = lines[i]
            # previous-msgid комментарий остаётся от fuzzy-match — он больше не нужен
            if line.startswith('#| '):
                i += 1
                continue
            if line.startswith('#, '):
                flags = [f.strip() for f in line[3:].split(',') if f.strip() != 'fuzzy']
                if flags:
                    out.append('#, ' + ', '.join(flags))
                i += 1
                continue
            if line.startswith('msgid '):
                msgid, i = _read_multiline(lines, i, 'msgid')
                out.append('msgid ' + _quote(msgid))
                continue
            if line.startswith('msgstr '):
                current, i = _read_multiline(lines, i, 'msgstr')
                # Заголовочный блок (msgid "") не трогаем.
                new = msgid if msgid else current
                out.append('msgstr ' + _quote(new))
                touched = touched or new != current
                continue
            out.append(line)
            i += 1

        blocks[bi] = '\n'.join(out)
        if touched:
            filled += 1

    PO_PATH.write_text('\n\n'.join(blocks), encoding='utf-8')
    print(f'ru: синхронизировано записей — {filled}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
