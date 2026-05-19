"""FooterPage edit-форма: intro_text (RU/KK/EN) + URL соцсетей."""

from django import forms

from pages.models import FooterPage

from .._common import (
    _apply_backoffice_widget_classes,
    _localized,
)


FOOTER_TRANSLATABLE = (
    'intro_text',
)


class FooterPageEditForm(forms.ModelForm):
    FORM_ID = 'footer-edit-form'

    class Meta:
        model = FooterPage
        fields = (
            'facebook_url',
            'instagram_url',
            'threads_url',
            'telegram_url',
        ) + _localized(*FOOTER_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
