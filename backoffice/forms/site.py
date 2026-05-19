"""Sidebar «Сайт» → раздел «Меню». NavSection + NavItem (inline)."""

from django import forms
from django.forms import inlineformset_factory

from navigation.models import NavItem, NavSection

from ._common import (
    _apply_backoffice_widget_classes,
    _localized,
)


NAV_SECTION_TRANSLATABLE = ('label',)
NAV_ITEM_TRANSLATABLE = ('label',)


class NavSectionEditForm(forms.ModelForm):
    """Секция мегаменю — slug+label×3+order. Slug — обязательный,
    видим (не hidden), потому что секций мало (1-3) и slug — стабильный
    идентификатор для разработчиков (используется в CSS-классах/JS)."""

    class Meta:
        model = NavSection
        fields = ('slug', 'order') + _localized(*NAV_SECTION_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        self.fields['slug'].widget.attrs['class'] = 'bo-input bo-input-mono'


class NavItemEditForm(forms.ModelForm):
    """Пункт навигации. Slug видимый (стабильный для active_page подсветки).
    `url_name` и `flat_page` — взаимоисключающие в логике (flat_page приоритет),
    но валидация мягкая: пустые оба — placeholder с href="#".

    `order` — hidden (управляется через DnD в шаблоне)."""

    class Meta:
        model = NavItem
        fields = (
            'slug',
            'url_name',
            'flat_page',
            'is_top_nav',
            'is_published',
            'order',
        ) + _localized(*NAV_ITEM_TRANSLATABLE)
        widgets = {
            'order': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        self.fields['order'].required = False
        self.fields['slug'].widget.attrs['class'] = 'bo-input bo-input-mono'
        self.fields['url_name'].widget.attrs['class'] = 'bo-input bo-input-mono'
        self.fields['url_name'].widget.attrs['placeholder'] = 'pages:about (или пусто, если задана FlatPage)'
        # flat_page — modelchoicefield, стандартный select
        self.fields['flat_page'].widget.attrs['class'] = 'bo-select'


NavItemFormSet = inlineformset_factory(
    parent_model=NavSection,
    model=NavItem,
    form=NavItemEditForm,
    extra=1,
    can_delete=True,
)


class NavSectionCreateForm(forms.ModelForm):
    """Минимальная форма создания секции: slug + label_ru + order. KK/EN/order
    можно дозаполнить на edit."""

    class Meta:
        model = NavSection
        fields = ('slug', 'order', 'label_ru')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        self.fields['slug'].widget.attrs['class'] = 'bo-input bo-input-mono'
        self.fields['label_ru'].required = True

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.label = self.cleaned_data.get('label_ru') or ''
        if commit:
            obj.save()
        return obj
