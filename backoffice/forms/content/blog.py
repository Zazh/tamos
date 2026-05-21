"""Blog edit-форма + taxonomy (category/tag) формы.

Категории и теги — глобальные (миграции 0006-0008): одни на все регионы.
Теги передаются hidden-полем `tags_json` со списком `[{slug, name, names?}]`,
view парсит и синхронизирует M2M через `_sync_blog_post_tags`.

SEO/OG/Публикация/Теги рендерятся ВНЕ основной `<form>` — связь через
HTML5 `form="blog-edit-form"`.
"""

import json

from django import forms

from blog.models import BlogCategory, BlogPost, BlogTag
from core.image_optimize import normalize_uploaded_image

from .._common import (
    FileSizeMixin,
    _apply_backoffice_widget_classes,
    _localized,
    apply_out_of_form_attrs,
    hide_slug_field,
    setup_region_field,
)


BLOG_POST_TRANSLATABLE = (
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

# SEO/OG поля рендерятся в отдельной панели ВНЕ основной формы. Шаблон знает
# этот список и кладёт нужные include'ы в правильное место.
BLOG_POST_OUT_OF_FORM_BASES = (
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)


class BlogPostEditForm(FileSizeMixin, forms.ModelForm):
    HTML_FIELDS = frozenset({'content'})
    COMPACT_FIELDS = frozenset({
        'seo_title', 'og_title',
        'cover_caption', 'cover_alt',
    })
    OUT_OF_FORM_BASES = frozenset({
        'seo_title', 'seo_description', 'og_title', 'og_description',
    })
    OUT_OF_FORM_FILE_FIELDS = frozenset({
        'og_image', 'is_published', 'published_at', 'tags_json',
    })
    FORM_ID = 'blog-edit-form'

    IMAGE_MAX_BYTES = 5 * 1024 * 1024

    tags_json = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        initial='[]',
    )

    class Meta:
        model = BlogPost
        fields = (
            'region',
            'category',
            'author',
            'slug',
            'cover_image',
            'og_image',
            'is_published',
            'published_at',
        ) + _localized(*BLOG_POST_TRANSLATABLE)
        widgets = {
            'published_at': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'bo-input',
            }),
            'is_published': forms.CheckboxInput(),
        }

    def __init__(self, *args, user=None, region=None, **kwargs):
        """`user`/`region` оставлены для совместимости с create-view;
        категории/теги теперь глобальные, region-фильтр не применяется."""
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

        # Категории — глобальные, без фильтра по региону.
        self.fields['category'].queryset = BlogCategory.objects.all().order_by('order', 'name')
        self.fields['category'].widget.attrs['class'] = 'bo-select'

        # Автор — член команды того же региона что и пост. Опционально (null=True).
        from team.models import TeamMember
        instance_for_author = kwargs.get('instance')
        if instance_for_author and instance_for_author.pk and instance_for_author.region_id:
            self.fields['author'].queryset = (
                TeamMember.objects
                .filter(region_id=instance_for_author.region_id, is_published=True)
                .order_by('order', 'name')
            )
        else:
            # На create: ограничиваем регионом менеджера если есть; для su — пусто
            # (поле автора на create.html не рендерится, заполняется на edit).
            if user is not None and getattr(user, 'manager_region_id', None):
                self.fields['author'].queryset = (
                    TeamMember.objects
                    .filter(region_id=user.manager_region_id, is_published=True)
                    .order_by('order', 'name')
                )
            else:
                self.fields['author'].queryset = TeamMember.objects.none()
        self.fields['author'].widget.attrs['class'] = 'bo-select'
        self.fields['author'].empty_label = '— не указан —'

        setup_region_field(self, user=user, instance=kwargs.get('instance'))

        # `datetime-local` ждёт ISO-формат без таймзоны.
        if self.instance and self.instance.pk and self.instance.published_at:
            self.initial['published_at'] = self.instance.published_at.strftime('%Y-%m-%dT%H:%M')

        # Pre-fill tags_json из текущей M2M (для GET).
        if self.instance and self.instance.pk:
            tags = [
                {
                    'slug': t.slug,
                    'name': t.name,
                    'names': {
                        'ru': t.name_ru or t.name or '',
                        'kk': t.name_kk or '',
                        'en': t.name_en or '',
                    },
                }
                for t in self.instance.tags.all().order_by('order', 'name')
            ]
            self.initial['tags_json'] = json.dumps(tags, ensure_ascii=False)

    def clean_cover_image(self):
        f = self._check_size(
            self.cleaned_data.get('cover_image'), self.IMAGE_MAX_BYTES, 'Обложка',
        )
        return normalize_uploaded_image(f)

    def clean_og_image(self):
        return self._check_size(
            self.cleaned_data.get('og_image'), self.IMAGE_MAX_BYTES, 'OG-картинка',
        )

    def clean_tags_json(self):
        """Валидирует JSON, возвращает уже распарсенный список dict'ов
        `[{slug, name, names?}]` — view использует их для sync M2M."""
        raw = self.cleaned_data.get('tags_json') or '[]'
        try:
            parsed = json.loads(raw)
        except ValueError:
            raise forms.ValidationError('Невалидный JSON списка тегов.')
        if not isinstance(parsed, list):
            raise forms.ValidationError('Список тегов должен быть массивом.')

        cleaned: list[dict] = []
        seen: set[str] = set()
        for item in parsed[:30]:
            if not isinstance(item, dict):
                continue
            slug = str(item.get('slug', '')).strip().lower()
            name = str(item.get('name', '')).strip()
            if not slug or not name or slug in seen:
                continue
            safe_slug = ''.join(c for c in slug if c.isalnum() or c == '-')[:64].strip('-')
            if not safe_slug:
                continue
            seen.add(safe_slug)
            entry = {'slug': safe_slug, 'name': name[:80]}
            raw_names = item.get('names') if isinstance(item.get('names'), dict) else None
            if raw_names:
                entry['names'] = {
                    lang: str(raw_names.get(lang, ''))[:80]
                    for lang in ('ru', 'kk', 'en')
                }
            cleaned.append(entry)
        return cleaned


class BlogCategoryItemForm(forms.ModelForm):
    """Inline-форма для редактирования одной BlogCategory на странице taxonomy.
    Order/slug пользователю не показываем."""

    class Meta:
        model = BlogCategory
        fields = _localized('name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


class BlogTagItemForm(forms.ModelForm):
    class Meta:
        model = BlogTag
        fields = _localized('name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


class BlogCategoryCreateForm(forms.Form):
    """Быстрое создание новой BlogCategory из taxonomy-страницы. Глобальная,
    без region. Slug автогенерится."""

    name_ru = forms.CharField(max_length=80, widget=forms.TextInput(attrs={'class': 'bo-input'}))

    def __init__(self, *args, user=None, **kwargs):
        # `user` оставлен для совместимости с view; не используется.
        super().__init__(*args, **kwargs)


class BlogTagCreateForm(BlogCategoryCreateForm):
    """То же что BlogCategoryCreateForm — одинаковая структура."""
    pass
