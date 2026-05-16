from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from feedback.models import Lead
from pages.models import (
    ContactsDepartment,
    ContactsPage,
    HomePage,
)


# Языки modeltranslation для backoffice-форм. Источник правды — settings.
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


def _apply_backoffice_widget_classes(form, *, html_fields=()):
    """Прокинуть нужный bo-class на каждый widget формы — чтобы шаблон не
    рендерил input'ы вручную, а просто ставил `{{ form.field }}` где надо.

    Также для translatable полей расставляет placeholder с подсказкой
    fallback на ru.
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
            attrs['class'] = ' '.join(classes)
            attrs.setdefault('rows', 4)
        elif isinstance(widget, (forms.NumberInput, forms.TextInput,
                                 forms.EmailInput, forms.URLInput)):
            attrs['class'] = 'bo-input'
        elif isinstance(widget, forms.ClearableFileInput):
            attrs['class'] = 'bo-file-input'
        # CheckboxInput (DELETE) и прочие — без класса.

        if is_translation and lang != 'ru' and 'placeholder' not in attrs:
            attrs['placeholder'] = '(пусто — берётся из ru)'


class LoginForm(forms.Form):
    username = forms.CharField(
        label=_('Логин'),
        max_length=150,
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'autocomplete': 'username',
            'autocapitalize': 'off',
            'autocorrect': 'off',
            'spellcheck': 'false',
        }),
    )
    password = forms.CharField(
        label=_('Пароль'),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )

    error_messages = {
        'invalid_login': _('Неверный логин или пароль.'),
        'no_access': _('У этой учётной записи нет доступа в backoffice.'),
        'inactive': _('Учётная запись отключена.'),
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(self.error_messages['invalid_login'], code='invalid_login')
            if not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages['inactive'], code='inactive')
            if not self.user_cache.is_staff:
                raise forms.ValidationError(self.error_messages['no_access'], code='no_access')
        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class LeadEditForm(forms.ModelForm):
    """Редактирование заявки в backoffice.

    Контактные поля (name/phone/city/origin/title) — read-only в шаблоне,
    форма ими не управляет. Менеджер меняет: статус, категория, заметка.
    """

    class Meta:
        model = Lead
        fields = ('status', 'category', 'manager_note')
        widgets = {
            'manager_note': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Что по звонку, договорённости, причина отказа.',
            }),
        }


# ===== Content: HomePage / ContactsPage edit forms ===========================
#
# Каждое translatable поле в форме разворачивается в три (`_ru`, `_kk`, `_en`).
# Шаблон рендерит их вручную с Alpine `x-show="lang === '..'"` — тогда у нас
# одна форма с правильным name'ом и POST с тремя значениями за раз.
#
# region не редактируется (singleton; menu-нав определяет регион). updated_at
# auto_now — не в форме.

_HOME_TRANSLATABLE = (
    'hero_badge_text',
    'hero_title',
    'hero_subtitle',
    'hero_cta_primary_text',
    'hero_cta_primary_modal_title',
    'hero_cta_secondary_text',
    'hero_cta_secondary_modal_title',
    'about_label',
    'about_title',
    'about_body',
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)


class HomePageEditForm(forms.ModelForm):
    """Редактирование HomePage с явными `_ru/_kk/_en` полями для каждого поля
    из translation.py."""

    HTML_FIELDS = frozenset({'hero_title'})

    # Server-side лимиты на каждый файл-апроад (доп. защита поверх глобального
    # DATA_UPLOAD_MAX_MEMORY_SIZE в settings).
    IMAGE_MAX_BYTES = 5 * 1024 * 1024
    VIDEO_MAX_BYTES = 35 * 1024 * 1024

    class Meta:
        model = HomePage
        fields = ('hero_image', 'video_file', 'og_image') + _localized(*_HOME_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self, html_fields=self.HTML_FIELDS)

    def _check_max_size(self, file, limit, kind):
        """Soft size-проверка для одного файла. Если файл превышает лимит —
        бросаем ValidationError с понятной подсказкой (где сжать).

        `file` приходит как `UploadedFile` (есть атрибут .size). Если поле
        не менялось — это FieldFile с .size, обращаемся аккуратно."""
        if not file or not hasattr(file, 'size'):
            return file
        mb = file.size / 1024 / 1024
        limit_mb = limit // (1024 * 1024)
        if file.size > limit:
            raise forms.ValidationError(
                f'Файл {mb:.1f} MB больше лимита {limit_mb} MB для «{kind}». '
                'Сожми через CloudConvert / TinyPNG / HandBrake.'
            )
        return file

    def clean_hero_image(self):
        return self._check_max_size(self.cleaned_data.get('hero_image'),
                                    self.IMAGE_MAX_BYTES, 'hero')

    def clean_og_image(self):
        return self._check_max_size(self.cleaned_data.get('og_image'),
                                    self.IMAGE_MAX_BYTES, 'OG-картинка')

    def clean_video_file(self):
        return self._check_max_size(self.cleaned_data.get('video_file'),
                                    self.VIDEO_MAX_BYTES, 'шоурил')


_CONTACTS_TRANSLATABLE = (
    'intro_title',
    'intro_text',
    'office_name',
    'office_address',
    'office_hours',
)


class ContactsPageEditForm(forms.ModelForm):
    class Meta:
        model = ContactsPage
        fields = (
            'latitude',
            'longitude',
            'map_zoom',
        ) + _localized(*_CONTACTS_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


_CONTACTS_DEPARTMENT_TRANSLATABLE = ('title', 'description', 'hours')


class ContactsDepartmentItemForm(forms.ModelForm):
    class Meta:
        model = ContactsDepartment
        fields = (
            'order',
            'phone',
            'email',
        ) + _localized(*_CONTACTS_DEPARTMENT_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


ContactsDepartmentFormSet = inlineformset_factory(
    parent_model=ContactsPage,
    model=ContactsDepartment,
    form=ContactsDepartmentItemForm,
    extra=1,
    can_delete=True,
)
