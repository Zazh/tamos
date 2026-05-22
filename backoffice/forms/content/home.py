"""HomePage edit-форма. Все translatable поля развёрнуты в _ru/_kk/_en
(шаблон рендерит их вручную с Alpine `x-show="lang === '..'"` — одна форма,
один POST с тремя значениями за раз).

SEO/OG-блок рендерится после галереи (вне основного `<form id="home-edit-form">`)
— HTML5 form= возвращает поля в submit.

Region и updated_at в форме отсутствуют: singleton per region (region
определяется menu-нав'ом), updated_at — auto_now.
"""

from django import forms

from pages.models import HomePage

from .._common import (
    FileSizeMixin,
    _apply_backoffice_widget_classes,
    _localized,
    apply_out_of_form_attrs,
)


HOME_TRANSLATABLE = (
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


class HomePageEditForm(FileSizeMixin, forms.ModelForm):
    HTML_FIELDS = frozenset({'hero_title'})

    OUT_OF_FORM_BASES = frozenset({
        'seo_title', 'seo_description', 'og_title', 'og_description',
    })
    OUT_OF_FORM_FILE_FIELDS = frozenset()
    FORM_ID = 'home-edit-form'

    # Server-side лимиты на загрузку (доп. защита поверх DATA_UPLOAD_MAX_MEMORY_SIZE).
    IMAGE_MAX_BYTES = 5 * 1024 * 1024
    VIDEO_MAX_BYTES = 35 * 1024 * 1024

    class Meta:
        model = HomePage
        fields = ('hero_image', 'video_file') + _localized(*HOME_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self, html_fields=self.HTML_FIELDS)
        apply_out_of_form_attrs(
            self, self.FORM_ID, self.OUT_OF_FORM_BASES, self.OUT_OF_FORM_FILE_FIELDS,
        )

    def clean_hero_image(self):
        return self._check_size(self.cleaned_data.get('hero_image'),
                                self.IMAGE_MAX_BYTES, 'hero')

    def clean_video_file(self):
        return self._check_size(self.cleaned_data.get('video_file'),
                                self.VIDEO_MAX_BYTES, 'шоурил')
