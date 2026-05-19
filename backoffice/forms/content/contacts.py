"""ContactsPage edit-форма + inline Department. Структурно повторяет
HomePage: SEO/OG рендерится после inline-formset Departments, поэтому
HTML5 form= возвращает поля в основной submit.
"""

from django import forms
from django.forms import inlineformset_factory

from pages.models import ContactsDepartment, ContactsPage

from .._common import (
    FileSizeMixin,
    _apply_backoffice_widget_classes,
    _localized,
    apply_out_of_form_attrs,
)


CONTACTS_TRANSLATABLE = (
    'intro_title',
    'intro_text',
    'office_name',
    'office_address',
    'office_hours',
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)


class ContactsPageEditForm(FileSizeMixin, forms.ModelForm):
    OUT_OF_FORM_BASES = frozenset({
        'seo_title', 'seo_description', 'og_title', 'og_description',
    })
    OUT_OF_FORM_FILE_FIELDS = frozenset({'og_image'})
    FORM_ID = 'contacts-edit-form'

    IMAGE_MAX_BYTES = 5 * 1024 * 1024

    class Meta:
        model = ContactsPage
        fields = (
            'latitude',
            'longitude',
            'map_zoom',
            'og_image',
        ) + _localized(*CONTACTS_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        apply_out_of_form_attrs(
            self, self.FORM_ID, self.OUT_OF_FORM_BASES, self.OUT_OF_FORM_FILE_FIELDS,
        )

    def clean_og_image(self):
        return self._check_size(self.cleaned_data.get('og_image'),
                                self.IMAGE_MAX_BYTES, 'OG-картинка')


_CONTACTS_DEPARTMENT_TRANSLATABLE = ('title', 'description', 'hours')


class ContactsDepartmentItemForm(forms.ModelForm):
    class Meta:
        model = ContactsDepartment
        fields = (
            'order',
            'phone',
            'email',
        ) + _localized(*_CONTACTS_DEPARTMENT_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)


ContactsDepartmentFormSet = inlineformset_factory(
    parent_model=ContactsPage,
    model=ContactsDepartment,
    form=ContactsDepartmentItemForm,
    extra=1,
    can_delete=True,
)
