"""TeamMember edit-форма. Одна модель TeamMember с фото и SEO. Region-scoped.

SEO/OG + «Публикация» (is_published / is_featured / teaches_*) рендерятся ВНЕ
основного `<form>` — связь через HTML5 `form="team-edit-form"`.
"""

from django import forms
from PIL import Image

from team.models import TeamMember, TEAM_PHOTO_MAX_DIMENSION

from .._common import (
    FileSizeMixin,
    _apply_backoffice_widget_classes,
    _localized,
    apply_out_of_form_attrs,
    hide_slug_field,
    setup_region_field,
)


TEAM_MEMBER_TRANSLATABLE = (
    'name',
    'role',
    'meta',
    'quote',
    'bio',
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)

TEAM_MEMBER_OUT_OF_FORM_BASES = (
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)


class TeamMemberEditForm(FileSizeMixin, forms.ModelForm):
    HTML_FIELDS = frozenset({'bio'})
    COMPACT_FIELDS = frozenset({
        'name', 'role', 'meta',
        'seo_title', 'og_title',
    })
    OUT_OF_FORM_BASES = frozenset({
        'seo_title', 'seo_description', 'og_title', 'og_description',
    })
    OUT_OF_FORM_FILE_FIELDS = frozenset({
        'og_image', 'is_published', 'is_featured', 'is_admin',
        'teaches_primary', 'teaches_middle', 'teaches_senior',
        'linkedin_url',
    })
    FORM_ID = 'team-edit-form'

    IMAGE_MAX_BYTES = 5 * 1024 * 1024
    # Минимальная сторона исходника. ImageSpec ужимает фото до
    # TEAM_PHOTO_MAX_DIMENSION (1024) с upscale=False, поэтому загружать
    # фото меньше — оно останется маленьким и будет мылиться на retina.
    PHOTO_MIN_DIMENSION = TEAM_PHOTO_MAX_DIMENSION

    class Meta:
        model = TeamMember
        # `order` намеренно отсутствует — порядок задаётся только через DnD
        # на странице region (см. `content_team_reorder`).
        fields = (
            'region',
            'slug',
            'photo',
            'linkedin_url',
            'teaches_primary',
            'teaches_middle',
            'teaches_senior',
            'is_admin',
            'og_image',
            'is_published',
            'is_featured',
        ) + _localized(*TEAM_MEMBER_TRANSLATABLE)
        widgets = {
            'is_published': forms.CheckboxInput(),
            'is_featured': forms.CheckboxInput(),
            'is_admin': forms.CheckboxInput(),
            'teaches_primary': forms.CheckboxInput(),
            'teaches_middle': forms.CheckboxInput(),
            'teaches_senior': forms.CheckboxInput(),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'bo-input',
                'placeholder': 'https://www.linkedin.com/in/…',
            }),
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

    def clean_photo(self):
        photo = self._check_size(self.cleaned_data.get('photo'),
                                 self.IMAGE_MAX_BYTES, 'Фото')
        uploaded = self.files.get('photo')
        if uploaded is not None:
            try:
                uploaded.seek(0)
                with Image.open(uploaded) as im:
                    w, h = im.size
            finally:
                uploaded.seek(0)
            min_dim = self.PHOTO_MIN_DIMENSION
            if min(w, h) < min_dim:
                raise forms.ValidationError(
                    f'Фото слишком маленькое: {w}×{h}px. '
                    f'Минимум {min_dim}×{min_dim}px — иначе на странице '
                    f'команды и в retina-дисплеях оно будет мылиться.'
                )
        return photo

    def clean_og_image(self):
        return self._check_size(self.cleaned_data.get('og_image'),
                                self.IMAGE_MAX_BYTES, 'OG-картинка')
