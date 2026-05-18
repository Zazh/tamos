"""Авто-перевод всего контента раздела «Активности» через Gemini.

Покрывает:
- `ActivitySection.title` (3 секции, global)
- `Activity.name` / `description` / `location` (per-region)
- `ActivityGroup.label` / `teacher_bio` (per-group)

ФИО (`ActivityGroup.teacher_name`) НЕ переводим — для каждой группы копируем
ru → kk/en если пустое. Имена не локализуются буквально (был бы транслит/
искажение), а копия — достаточно безопасный дефолт. Менеджер может позже
поправить написание на казахском/английском вручную.

Аргументы:
  --region <slug>        — переводить только активности этого региона.
  --reset-aktau-teachers — перед переводом установить teacher_name =
                           «Не назначен» (RU/KK/EN) и очистить phone/bio
                           для всех групп Актау.
  --force                — переводить даже непустые kk/en (перезаписать).
                           По умолчанию пропускаем уже заполненные поля.
  --dry-run              — печатать что бы перевели, без вызова Gemini и save.

Пример: python manage.py translate_activities --reset-aktau-teachers
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from activities.models import Activity, ActivityGroup, ActivitySection
from core.gemini_translate import (
    TranslationConfigError,
    TranslationError,
    translate_fields,
)


LANGS = ('kk', 'en')


# Фиксированные локализованные значения «Не назначен» — не идут через Gemini,
# чтобы избежать неконсистентности (LLM может выдать варианты).
UNASSIGNED = {
    'ru': 'Не назначен',
    'kk': 'Тағайындалмаған',
    'en': 'Not assigned',
}


class Command(BaseCommand):
    help = 'Авто-перевод RU→KK/EN всего контента раздела «Активности».'

    def add_arguments(self, parser):
        parser.add_argument('--region', help='Slug региона (опционально).')
        parser.add_argument(
            '--reset-aktau-teachers',
            action='store_true',
            help='Сначала «обнулить» тренеров для всех групп Актау (teacher_name = «Не назначен»).',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Перезаписать непустые kk/en переводы. По умолчанию пропускаются.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Не вызывать Gemini и не сохранять — только напечатать что бы сделали.',
        )

    def handle(self, *args, **opts):
        self.region_slug = opts.get('region')
        self.force = opts.get('force', False)
        self.dry_run = opts.get('dry_run', False)

        if opts.get('reset_aktau_teachers'):
            self._reset_aktau_teachers()

        self._translate_sections()
        self._translate_activities()
        self._translate_groups()
        self.stdout.write(self.style.SUCCESS('Готово.'))

    # ----- Aktau teacher reset -------------------------------------------

    def _reset_aktau_teachers(self):
        groups = ActivityGroup.objects.filter(activity__region__slug='aktau')
        n = 0
        for g in groups:
            g.teacher_name = UNASSIGNED['ru']
            g.teacher_name_ru = UNASSIGNED['ru']
            g.teacher_name_kk = UNASSIGNED['kk']
            g.teacher_name_en = UNASSIGNED['en']
            g.teacher_phone = ''
            g.teacher_bio = ''
            g.teacher_bio_ru = ''
            g.teacher_bio_kk = ''
            g.teacher_bio_en = ''
            if not self.dry_run:
                g.save(update_fields=[
                    'teacher_name',
                    'teacher_name_ru', 'teacher_name_kk', 'teacher_name_en',
                    'teacher_phone',
                    'teacher_bio', 'teacher_bio_ru', 'teacher_bio_kk', 'teacher_bio_en',
                ])
            n += 1
        prefix = '[dry-run] ' if self.dry_run else ''
        self.stdout.write(f'{prefix}Aktau: установлено «Не назначен» для {n} групп.')

    # ----- Translation ----------------------------------------------------

    def _translate_object(self, obj, bases, label):
        """Для одного объекта собрать пары (base, ru) для kk/en и одним вызовом
        каждого target lang получить переводы. Идемпотентно: если поле
        `<base>_<lang>` уже заполнено и нет `--force`, пропускаем.

        Возвращает True если был хоть один update (для логирования).
        """
        ru_values = {}
        for base in bases:
            ru = getattr(obj, f'{base}_ru', None) or getattr(obj, base, None) or ''
            ru = (ru or '').strip()
            if ru:
                ru_values[base] = ru

        if not ru_values:
            return False

        any_update = False
        for lang in LANGS:
            # Собираем только те базы, где целевой <base>_<lang> пуст (или --force).
            payload = {}
            for base, ru in ru_values.items():
                cur = getattr(obj, f'{base}_{lang}', None) or ''
                if cur and not self.force:
                    continue
                payload[base] = ru

            if not payload:
                continue

            if self.dry_run:
                self.stdout.write(f'  [dry-run] {label} → {lang}: {list(payload.keys())}')
                continue

            try:
                translated = translate_fields(payload, lang)
            except TranslationConfigError as e:
                self.stderr.write(self.style.ERROR(f'  CONFIG ERROR: {e}'))
                return any_update
            except TranslationError as e:
                self.stderr.write(self.style.WARNING(f'  {label} {lang}: {e}'))
                continue
            except Exception as e:
                # TimeoutError / прочие сетевые — не валим всю команду, идём дальше.
                self.stderr.write(self.style.WARNING(f'  {label} {lang}: skip ({type(e).__name__}: {e})'))
                continue

            update_fields = []
            for base, value in translated.items():
                setattr(obj, f'{base}_{lang}', value)
                update_fields.append(f'{base}_{lang}')
            if update_fields:
                obj.save(update_fields=update_fields)
                any_update = True
                self.stdout.write(f'  {label} → {lang}: {", ".join(update_fields)}')

        return any_update

    def _translate_sections(self):
        self.stdout.write(self.style.NOTICE('=== Секции (Activity Section) ==='))
        for s in ActivitySection.objects.order_by('order', 'slug'):
            self._translate_object(s, ['title'], f'Section[{s.slug}]')

    def _translate_activities(self):
        self.stdout.write(self.style.NOTICE('=== Activity (name/description/location) ==='))
        qs = Activity.objects.select_related('region').order_by('region__slug', 'section__order', 'order')
        if self.region_slug:
            qs = qs.filter(region__slug=self.region_slug)
        for a in qs:
            self._translate_object(
                a,
                ['name', 'description', 'location'],
                f'Activity[{a.region.slug}/{a.pk}: {a.name_ru or a.name}]',
            )

    def _translate_groups(self):
        self.stdout.write(self.style.NOTICE('=== ActivityGroup (label/teacher_bio + ФИО копированием) ==='))
        qs = ActivityGroup.objects.select_related('activity__region').order_by(
            'activity__region__slug', 'activity__section__order', 'activity__order', 'order',
        )
        if self.region_slug:
            qs = qs.filter(activity__region__slug=self.region_slug)
        for g in qs:
            label_for_log = f'Group[{g.activity.region.slug}/{g.pk}: {g.label_display or g.activity.name}]'

            # 1) teacher_name — НЕ через Gemini, копируем ru → kk/en если пустое.
            self._copy_teacher_name(g, label_for_log)

            # 2) Остальное (label, teacher_bio) — через Gemini.
            self._translate_object(g, ['label', 'teacher_bio'], label_for_log)

    def _copy_teacher_name(self, g, label_for_log):
        """ФИО не переводим. Если ru заполнено и kk/en пустые — копируем."""
        ru = (g.teacher_name_ru or g.teacher_name or '').strip()
        if not ru:
            return
        update_fields = []
        for lang in LANGS:
            cur = getattr(g, f'teacher_name_{lang}', None) or ''
            if cur and not self.force:
                continue
            setattr(g, f'teacher_name_{lang}', ru)
            update_fields.append(f'teacher_name_{lang}')
        if update_fields and not self.dry_run:
            g.save(update_fields=update_fields)
            self.stdout.write(f'  {label_for_log} teacher_name: copy ru→{",".join(l[-2:] for l in update_fields)}')
        elif update_fields and self.dry_run:
            self.stdout.write(f'  [dry-run] {label_for_log} teacher_name: copy ru→{",".join(l[-2:] for l in update_fields)}')
