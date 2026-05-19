"""Sidebar «Настройки» → разделы «Регионы» и «Пользователи».

Доступ только для superuser (см. [[backoffice.views.settings]]).
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    password_validators_help_texts,
    validate_password,
)

from regions.models import Region

from ._common import (
    _apply_backoffice_widget_classes,
    _localized,
)


REGION_TRANSLATABLE = ('name',)


# ----- Регионы --------------------------------------------------------------


class RegionEditForm(forms.ModelForm):
    """Полная edit-форма: slug + name×3 + is_default + is_active.

    `is_default` валидируется на уровне БД (UniqueConstraint where is_default=True);
    форма не блокирует — при попытке сохранить второй default БД выбросит
    IntegrityError, view ловит и возвращает понятную ошибку.
    """

    class Meta:
        model = Region
        fields = ('slug', 'is_default', 'is_active') + _localized(*REGION_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        self.fields['slug'].widget.attrs['class'] = 'bo-input bo-input-mono'


class RegionCreateForm(forms.ModelForm):
    """Создание региона: slug + name_ru. KK/EN/флаги — на edit.

    `is_default` НЕ выставляется на create (нельзя сразу сделать default —
    это глобальное переключение, отдельный шаг через edit).
    """

    class Meta:
        model = Region
        fields = ('slug', 'name_ru', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        self.fields['slug'].widget.attrs['class'] = 'bo-input bo-input-mono'
        self.fields['name_ru'].required = True

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.name = self.cleaned_data.get('name_ru') or ''
        if commit:
            obj.save()
        return obj


# ----- Пользователи ---------------------------------------------------------


User = get_user_model()


# Семантические роли — UI-обёртка над тройкой флагов
# (is_staff, is_superuser, manager_region).
ROLE_SUPERADMIN = 'superadmin'
ROLE_MANAGER = 'manager'
ROLE_NONE = 'none'

ROLE_CHOICES = [
    (ROLE_SUPERADMIN, 'Суперадмин'),
    (ROLE_MANAGER, 'Менеджер региона'),
    (ROLE_NONE, 'Без доступа'),
]

ROLE_DESCRIPTIONS = {
    ROLE_SUPERADMIN: 'Видит весь backoffice, все регионы. Полный контроль над сайтом, пользователями, настройками.',
    ROLE_MANAGER: 'Видит только свой регион в backoffice. Не может редактировать меню, регионы и других пользователей.',
    ROLE_NONE: 'Не может войти в backoffice. Аккаунт хранится, но заблокирован.',
}


def _detect_role(instance):
    """Из тройки флагов instance → одна из ROLE_*. Используется на init."""
    if instance is None or not instance.pk:
        return ROLE_MANAGER  # дефолт для нового
    if instance.is_superuser:
        return ROLE_SUPERADMIN
    if instance.is_staff:
        return ROLE_MANAGER
    return ROLE_NONE


def _apply_role_to_instance(user, role, region):
    """Развернуть выбранную роль в тройку флагов user'а."""
    if role == ROLE_SUPERADMIN:
        user.is_staff = True
        user.is_superuser = True
        user.manager_region = None
    elif role == ROLE_MANAGER:
        user.is_staff = True
        user.is_superuser = False
        user.manager_region = region
    else:  # ROLE_NONE
        user.is_staff = False
        user.is_superuser = False
        user.manager_region = None


class _UserRoleMixin:
    """Общая логика role+manager_region для Edit/Create форм пользователей.

    Использует Form.cleaned_data + manager_region валидируется в зависимости
    от role: обязателен только для ROLE_MANAGER.
    """

    def _init_role_fields(self, *, lock_role=False):
        """Вызывается из __init__ после super().__init__(). lock_role=True
        блокирует выбор роли (для редактирования собственного аккаунта)."""
        self.fields['role'] = forms.ChoiceField(
            choices=ROLE_CHOICES,
            widget=forms.RadioSelect(attrs={'class': 'bo-role-radio'}),
            label='Роль',
            initial=_detect_role(self.instance),
        )
        self.fields['manager_region'].queryset = Region.objects.all()
        self.fields['manager_region'].widget.attrs['class'] = 'bo-select'
        self.fields['manager_region'].required = False
        if lock_role:
            # Сужаем choices до одной, чтобы UI отрисовал disabled-state;
            # запрос с другим значением → ValidationError на choice.
            current = _detect_role(self.instance)
            self.fields['role'].choices = [
                (v, l) for v, l in ROLE_CHOICES if v == current
            ]
            self.fields['role'].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('role')
        region = cleaned.get('manager_region')
        if role == ROLE_MANAGER and not region:
            self.add_error('manager_region', 'Для роли «Менеджер региона» нужно выбрать регион.')
        return cleaned


class UserEditForm(_UserRoleMixin, forms.ModelForm):
    """Профиль пользователя. Пароль отдельной формой/endpoint'ом."""

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'manager_region',
        )

    def __init__(self, *args, lock_role=False, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        self.fields['email'].required = False
        self._init_role_fields(lock_role=lock_role)

    def save(self, commit=True):
        user = super().save(commit=False)
        _apply_role_to_instance(
            user,
            self.cleaned_data.get('role'),
            self.cleaned_data.get('manager_region'),
        )
        if commit:
            user.save()
        return user


class UserCreateForm(_UserRoleMixin, forms.ModelForm):
    """Создание пользователя с паролем. Применяем стандартные validators."""

    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'bo-input', 'autocomplete': 'new-password'}),
        help_text=' '.join(password_validators_help_texts()),
    )
    password2 = forms.CharField(
        label='Пароль (ещё раз)',
        widget=forms.PasswordInput(attrs={'class': 'bo-input', 'autocomplete': 'new-password'}),
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'manager_region',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        self.fields['email'].required = False
        self.fields['is_active'].initial = True
        self._init_role_fields()

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Пароли не совпадают.')
        if p1 and p1 == p2:
            try:
                validate_password(p1)
            except forms.ValidationError as exc:
                raise forms.ValidationError(exc.messages)
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        _apply_role_to_instance(
            user,
            self.cleaned_data.get('role'),
            self.cleaned_data.get('manager_region'),
        )
        if commit:
            user.save()
        return user


class UserPasswordForm(forms.Form):
    """Только смена пароля. Используется отдельным endpoint'ом."""

    password1 = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'class': 'bo-input', 'autocomplete': 'new-password'}),
        help_text=' '.join(password_validators_help_texts()),
    )
    password2 = forms.CharField(
        label='Новый пароль (ещё раз)',
        widget=forms.PasswordInput(attrs={'class': 'bo-input', 'autocomplete': 'new-password'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Пароли не совпадают.')
        if p1 and p1 == p2:
            try:
                validate_password(p1, user=self.user)
            except forms.ValidationError as exc:
                raise forms.ValidationError(exc.messages)
        return p2

    def save(self):
        self.user.set_password(self.cleaned_data['password1'])
        self.user.save(update_fields=['password'])
        return self.user
