"""Auth-формы для backoffice. Login — отдельная форма с проверкой `is_staff`
поверх стандартной аутентификации (обычные пользователи не должны войти
в backoffice; см. `shortcuts.backoffice_required`).
"""

from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


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
