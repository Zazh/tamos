"""Gallery (album-based): Album edit + GalleryImage edit + Category create.

Album — region-scoped «пост» с темой (category, глобальная).
GalleryImage — фото внутри альбома; alt/caption редактируются inline в grid
(отдельный edit-страницы нет; `GalleryImageEditForm` оставлена для legacy
URL, если ещё рендерится где-то).
"""

from django import forms

from core.image_optimize import normalize_uploaded_image
from gallery.models import Album, GalleryCategory, GalleryImage

from .._common import (
    _apply_backoffice_widget_classes,
    _localized,
    setup_region_field,
)


# ----- Album ---------------------------------------------------------------

ALBUM_TRANSLATABLE = (
    'title',
    'lead',
)


class AlbumEditForm(forms.ModelForm):
    """Edit/Create альбома. На edit region/slug — hidden; на create — обычные
    поля (region select для su, slug auto-gen в view)."""

    COMPACT_FIELDS = frozenset({'lead'})
    IMAGE_MAX_BYTES = 5 * 1024 * 1024

    class Meta:
        model = Album
        fields = (
            'region',
            'category',
            'slug',
            'cover_image',
            'is_published',
        ) + _localized(*ALBUM_TRANSLATABLE)
        widgets = {
            'is_published': forms.CheckboxInput(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self, compact_fields=self.COMPACT_FIELDS)

        # Slug пользователю не показываем — auto-gen из title.
        self.fields['slug'].widget = forms.HiddenInput()
        self.fields['slug'].required = False

        # Category — глобальная.
        self.fields['category'].queryset = (
            GalleryCategory.objects.filter(is_published=True).order_by('order', 'name')
        )
        self.fields['category'].widget.attrs['class'] = 'bo-select'

        setup_region_field(self, user=user, instance=kwargs.get('instance'))

    def clean_cover_image(self):
        f = self.cleaned_data.get('cover_image')
        if f and hasattr(f, 'size') and f.size > self.IMAGE_MAX_BYTES:
            mb = f.size / 1024 / 1024
            limit_mb = self.IMAGE_MAX_BYTES // (1024 * 1024)
            raise forms.ValidationError(
                f'Обложка: файл {mb:.1f} MB больше лимита {limit_mb} MB.'
            )
        return normalize_uploaded_image(f)


# ----- GalleryImage (legacy single-photo edit) ------------------------------

GALLERY_IMAGE_TRANSLATABLE = (
    'alt',
    'caption',
)


class GalleryImageEditForm(forms.ModelForm):
    """Минимальный edit одного фото: alt/caption + is_wide + is_published.
    Album/region остаются как есть. В новой UI alt/caption редактируется inline
    в grid альбома — эта форма для legacy URL."""

    COMPACT_FIELDS = frozenset({'alt', 'caption'})

    class Meta:
        model = GalleryImage
        fields = (
            'is_wide',
            'is_published',
        ) + _localized(*GALLERY_IMAGE_TRANSLATABLE)
        widgets = {
            'is_wide': forms.CheckboxInput(),
            'is_published': forms.CheckboxInput(),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self, compact_fields=self.COMPACT_FIELDS)


# ----- Category taxonomy ---------------------------------------------------


class GalleryCategoryItemForm(forms.ModelForm):
    """Inline-форма для редактирования категории на странице taxonomy."""

    class Meta:
        model = GalleryCategory
        fields = _localized('name') + ('is_published',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


class GalleryCategoryCreateForm(forms.Form):
    """Быстрое создание новой GalleryCategory из taxonomy-страницы."""

    name_ru = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'class': 'bo-input'}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
