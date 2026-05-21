"""FlatPage edit-форма (региональная «доп. страница»: About / Uniform / Privacy).

Slug — семантический (about/uniform/privacy), линкуется в `NavItem.flat_page`
через FK. На create менеджер вводит slug сам (короткое латинское имя), на
edit slug — read-only badge в шаблоне + hidden в форме.
"""

from django import forms

from core.image_optimize import normalize_uploaded_image
from pages.models import FlatPage

from .._common import (
    FileSizeMixin,
    _apply_backoffice_widget_classes,
    _localized,
    apply_out_of_form_attrs,
    setup_region_field,
)


FLATPAGE_TRANSLATABLE = (
    'title',
    'lead',
    'cover_caption',
    'cover_alt',
    'content',
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)

FLATPAGE_OUT_OF_FORM_BASES = (
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)


class FlatPageEditForm(FileSizeMixin, forms.ModelForm):
    HTML_FIELDS = frozenset({'content'})
    COMPACT_FIELDS = frozenset({
        'seo_title', 'og_title',
        'cover_caption', 'cover_alt',
    })
    OUT_OF_FORM_BASES = frozenset({
        'seo_title', 'seo_description', 'og_title', 'og_description',
    })
    OUT_OF_FORM_FILE_FIELDS = frozenset({
        'og_image', 'is_published',
    })
    FORM_ID = 'flatpage-edit-form'

    IMAGE_MAX_BYTES = 5 * 1024 * 1024

    class Meta:
        model = FlatPage
        fields = (
            'region',
            'slug',
            'cover_image',
            'og_image',
            'is_published',
        ) + _localized(*FLATPAGE_TRANSLATABLE)
        widgets = {
            'is_published': forms.CheckboxInput(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(
            self,
            html_fields=self.HTML_FIELDS,
            compact_fields=self.COMPACT_FIELDS,
        )

        apply_out_of_form_attrs(
            self, self.FORM_ID, self.OUT_OF_FORM_BASES, self.OUT_OF_FORM_FILE_FIELDS,
        )

        instance = kwargs.get('instance')
        if instance and instance.pk:
            # edit: slug — hidden, регион тоже фиксирован
            self.fields['slug'].widget = forms.HiddenInput()
            self.fields['slug'].required = False
        else:
            # create: slug — обычный input с латинским паттерном
            self.fields['slug'].widget.attrs['class'] = 'bo-input'
            self.fields['slug'].widget.attrs['placeholder'] = 'about, uniform, food…'
            self.fields['slug'].widget.attrs['pattern'] = '[a-z0-9-]+'
            self.fields['slug'].widget.attrs['maxlength'] = '80'
            self.fields['slug'].required = True

        setup_region_field(self, user=user, instance=instance)

    def clean_slug(self):
        slug = (self.cleaned_data.get('slug') or '').strip().lower()
        if not slug:
            return slug
        # Только латиница/цифры/дефис — иначе URL получится с %-кодами.
        safe = ''.join(c for c in slug if c.isalnum() or c == '-')[:80].strip('-')
        if not safe:
            raise forms.ValidationError(
                'Slug должен содержать латинские буквы, цифры и дефисы.'
            )
        return safe

    def clean_cover_image(self):
        f = self._check_size(
            self.cleaned_data.get('cover_image'), self.IMAGE_MAX_BYTES, 'Обложка',
        )
        return normalize_uploaded_image(f)

    def clean_og_image(self):
        return self._check_size(
            self.cleaned_data.get('og_image'), self.IMAGE_MAX_BYTES, 'OG-картинка',
        )
