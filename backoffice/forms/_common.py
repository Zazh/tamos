"""Общие хелперы и mixin'ы для backoffice-форм.

Все ModelForm'ы здесь — translatable: `_localized(*bases)` разворачивает
базовые имена в `_ru/_kk/_en` тройки, `_apply_backoffice_widget_classes`
ставит CSS-классы на widget'ы и подсказку `(пусто — берётся из ru)` на
не-RU переводы.

Поверх этого — три повторяющихся паттерна, которые здесь же:
  * `FileSizeMixin.check_size` — проверка лимита на загружаемый файл.
  * `apply_out_of_form_attrs` — HTML5 `form="..."` для полей, которые
    рендерятся вне основного `<form>` (SEO/OG-блок, чекбокс публикации
    и т.п.). Без этого их значения не уходят в submit.
  * `setup_region_field` — на edit прячет region (hidden), на create
    показывает select, ограниченный manager_region (или всеми регионами
    для superuser).
"""

from django import forms
from django.conf import settings


TRANSLATION_LANGS = settings.MODELTRANSLATION_LANGUAGES  # ('ru', 'kk', 'en')


def _localized(*field_names):
    """Развернуть `('hero_title',)` в `('hero_title_ru', 'hero_title_kk', 'hero_title_en')`.

    Используется в Meta.fields для ModelForm на translatable моделях. Базовое
    (untranslated) поле не включаем — modeltranslation хранит данные в `_<lang>`
    колонках, а base используется только при чтении (резолвится по active language).
    """
    return tuple(f'{name}_{lang}' for name in field_names for lang in TRANSLATION_LANGS)


def _strip_lang(name):
    """`hero_title_ru` → `hero_title`. Для не-локализованных полей — без изменений."""
    for lang in TRANSLATION_LANGS:
        suffix = f'_{lang}'
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _apply_backoffice_widget_classes(form, *, html_fields=(), compact_fields=()):
    """Прокинуть нужный bo-class на каждый widget формы — чтобы шаблон не
    рендерил input'ы вручную, а просто ставил `{{ form.field }}` где надо.

    Также для translatable полей расставляет placeholder с подсказкой
    fallback на ru.

    Параметры:
      html_fields — base-имена textarea-полей с HTML-разметкой (rows=4 моноспейс).
      compact_fields — base-имена textarea-полей, которые визуально должны быть
        однострочными (заголовки/подзаголовки секций — TextField в модели только
        ради совместимости со старым content'ом, в UI это короткие однострочники).
        rows=1, без auto-resize вверх.
    """
    for name, field in form.fields.items():
        widget = field.widget
        attrs = widget.attrs
        base_name = _strip_lang(name)
        is_translation = base_name != name
        lang = name.split('_')[-1] if is_translation else None

        if isinstance(widget, forms.Textarea):
            classes = ['bo-textarea']
            if base_name in html_fields:
                classes.append('bo-textarea-html')
                attrs.setdefault('rows', 4)
            elif base_name in compact_fields:
                classes.append('bo-textarea-compact')
                attrs['rows'] = 1
            else:
                attrs.setdefault('rows', 2)
            attrs['class'] = ' '.join(classes)
        elif isinstance(widget, (forms.NumberInput, forms.TextInput,
                                 forms.EmailInput, forms.URLInput)):
            attrs['class'] = 'bo-input'
        elif isinstance(widget, forms.ClearableFileInput):
            attrs['class'] = 'bo-file-input'

        if is_translation and lang != 'ru' and 'placeholder' not in attrs:
            attrs['placeholder'] = '(пусто — берётся из ru)'


def _relax_required(form, bases):
    """Сделать `required=False` для всех `_ru/_kk/_en` полей перечисленных bases.

    Используется в inline-формах с фиксированным числом слотов (audience/benefit/
    cert/stat): менеджер может оставить слот пустым (placeholder для будущего
    контента). Публичный шаблон скрывает пустые карточки через `{% if item.title %}`.
    """
    for base in bases:
        for lang in TRANSLATION_LANGS:
            name = f'{base}_{lang}'
            if name in form.fields:
                form.fields[name].required = False


def _limit_chars(form, bases, limit):
    """Ограничить длину `_ru/_kk/_en` полей перечисленных bases.

    Источник правды для лимита — UX: длина должна быть такой, чтобы перевод
    RU→KK/EN (обычно +30…50% символов) гарантированно помещался в карточку.
    """
    for base in bases:
        for lang in TRANSLATION_LANGS:
            name = f'{base}_{lang}'
            if name in form.fields:
                form.fields[name].max_length = limit
                form.fields[name].widget.attrs['maxlength'] = limit


def apply_out_of_form_attrs(form, form_id, bases, file_fields=()):
    """Прокинуть HTML5 `form="<form_id>"` на поля, которые рендерятся ВНЕ
    основного `<form id="...">`.

    Без этого их значения не попадают в submit. Применяется к SEO/OG-блоку,
    панели «Публикация», `og_image` и т.п. — всё, что в шаблоне рендерится
    отдельным блоком вне `<form>`.

    Args:
      form_id: значение для атрибута `form="..."` на input.
      bases: набор базовых имён translatable полей (без `_ru/_kk/_en`).
      file_fields: точные имена нелокализуемых полей (`og_image`,
        `is_published`, …).
    """
    bases_set = set(bases)
    file_fields_set = set(file_fields)
    for name, field in form.fields.items():
        base = _strip_lang(name)
        if base in bases_set or name in file_fields_set:
            field.widget.attrs['form'] = form_id


def setup_region_field(form, *, user, instance):
    """Стандартный паттерн region на create/edit для region-scoped моделей.

    На edit (`instance.pk` есть) — `region` становится hidden и `required=False`
    (его значение восстанавливает view через `original_region_id` ДО init формы,
    см. [[feedback_modelform_mutates_instance]]).

    На create — select, ограниченный регионом менеджера (или всеми активными
    регионами для superuser). Если у менеджера нет региона — пустой queryset.
    """
    from regions.models import Region

    if instance and instance.pk:
        form.fields['region'].widget = forms.HiddenInput()
        form.fields['region'].required = False
        return

    if user is not None and user.is_superuser:
        form.fields['region'].queryset = Region.objects.filter(is_active=True)
    elif user is not None and getattr(user, 'manager_region_id', None):
        form.fields['region'].queryset = Region.objects.filter(pk=user.manager_region_id)
        form.fields['region'].initial = user.manager_region_id
    else:
        form.fields['region'].queryset = Region.objects.none()
    form.fields['region'].widget.attrs['class'] = 'bo-select'


def hide_slug_field(form):
    """Сделать `slug` hidden + `required=False` — стандарт для blog/event/
    flatpage(edit)/gallery/team. Slug автогенерируется в view'е (для blog/event/
    gallery/team) или вводится менеджером только на create (для flatpage)."""
    form.fields['slug'].widget = forms.HiddenInput()
    form.fields['slug'].required = False


class FileSizeMixin:
    """Mixin, дающий `_check_size(file, limit, label)` метод. Используется в
    `clean_<image_field>` для soft size-проверки.

    Класс-владелец задаёт лимит (`IMAGE_MAX_BYTES`) и вызывает
    `self._check_size(self.cleaned_data.get('field'), self.IMAGE_MAX_BYTES, 'Обложка')`.
    Если файл превышает — `ValidationError` с подсказкой где сжать.
    """

    SIZE_HINT = 'Сожми через CloudConvert / TinyPNG.'

    def _check_size(self, file, limit, label):
        if not file or not hasattr(file, 'size'):
            return file
        if file.size > limit:
            mb = file.size / 1024 / 1024
            limit_mb = limit // (1024 * 1024)
            raise forms.ValidationError(
                f'{label}: файл {mb:.1f} MB больше лимита {limit_mb} MB. {self.SIZE_HINT}'
            )
        return file
