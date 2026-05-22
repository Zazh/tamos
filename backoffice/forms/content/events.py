"""Event edit-форма. Структурно проще BlogPostEditForm: нет category/tags/
author/tags_json. SEO/OG + Публикация рендерятся ВНЕ основной формы.

Slug генерируется автоматически из title с 4-hex суффиксом (см.
views._auto_slug_for_event).
"""

from django import forms

from core.image_optimize import normalize_uploaded_image
from events.models import Event

from .._common import (
    FileSizeMixin,
    _apply_backoffice_widget_classes,
    _localized,
    apply_out_of_form_attrs,
    hide_slug_field,
    setup_region_field,
)


EVENT_TRANSLATABLE = (
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

EVENT_OUT_OF_FORM_BASES = (
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)


class EventEditForm(FileSizeMixin, forms.ModelForm):
    HTML_FIELDS = frozenset({'content'})
    COMPACT_FIELDS = frozenset({
        'seo_title', 'og_title',
        'cover_caption', 'cover_alt',
    })
    OUT_OF_FORM_BASES = frozenset({
        'seo_title', 'seo_description', 'og_title', 'og_description',
    })
    OUT_OF_FORM_FILE_FIELDS = frozenset({'is_published', 'published_at'})
    FORM_ID = 'event-edit-form'

    IMAGE_MAX_BYTES = 5 * 1024 * 1024

    class Meta:
        model = Event
        fields = (
            'region',
            'slug',
            'cover_image',
            'is_published',
            'published_at',
        ) + _localized(*EVENT_TRANSLATABLE)
        widgets = {
            'published_at': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'bo-input',
            }),
            'is_published': forms.CheckboxInput(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(
            self,
            html_fields=self.HTML_FIELDS,
            compact_fields=self.COMPACT_FIELDS,
        )

        hide_slug_field(self)

        apply_out_of_form_attrs(
            self, self.FORM_ID, self.OUT_OF_FORM_BASES, self.OUT_OF_FORM_FILE_FIELDS,
        )

        setup_region_field(self, user=user, instance=kwargs.get('instance'))

        # `datetime-local` ждёт ISO-формат без таймзоны.
        if self.instance and self.instance.pk and self.instance.published_at:
            self.initial['published_at'] = self.instance.published_at.strftime('%Y-%m-%dT%H:%M')

    def clean_cover_image(self):
        f = self._check_size(
            self.cleaned_data.get('cover_image'), self.IMAGE_MAX_BYTES, 'Обложка',
        )
        return normalize_uploaded_image(f)
