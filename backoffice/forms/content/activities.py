"""Activities (Activity / ActivityGroup / ScheduleSlot) edit-формы.

Структура (см. `memory/activities.md`):
  Region → ActivitySection (global) → Activity → ActivityGroup → ScheduleSlot

Тренер задаётся на УРОВНЕ ГРУППЫ (`ActivityGroup.teacher_*`), не на Activity.
"""

from django import forms
from django.forms import inlineformset_factory

from activities.models import Activity, ActivityGroup, ScheduleSlot

from .._common import (
    TRANSLATION_LANGS,
    _apply_backoffice_widget_classes,
    _localized,
)


ACTIVITY_TRANSLATABLE = ('name', 'description', 'location')
ACTIVITY_GROUP_TRANSLATABLE = ('label', 'teacher_name', 'teacher_bio')


class ActivityEditForm(forms.ModelForm):
    """Edit одного кружка. Тренер — на уровне группы, не здесь."""

    FORM_ID_TPL = 'activity-{pk}-form'
    COMPACT_FIELDS = frozenset({'name', 'location'})

    class Meta:
        model = Activity
        fields = (
            'section',
            'is_published',
            'is_featured',
            'order',
        ) + _localized(*ACTIVITY_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self, compact_fields=self.COMPACT_FIELDS)
        self.fields['section'].widget.attrs['class'] = 'bo-select'
        # Order — hidden (DnD сортировка в catalog).
        self.fields['order'].widget = forms.HiddenInput()
        # name — maxlength=60 на input уровне (модель тоже max_length=60).
        for lang in TRANSLATION_LANGS:
            name_field = f'name_{lang}'
            if name_field in self.fields:
                self.fields[name_field].widget.attrs['maxlength'] = 60


class ActivityGroupForm(forms.ModelForm):
    """Edit одной группы внутри activity. classes — multi-checkbox 1..11.

    Тренер (имя/телефон/био) — на уровне группы: у разных групп одного кружка
    могут быть разные тренеры.
    """

    classes = forms.MultipleChoiceField(
        choices=[(i, str(i)) for i in range(1, 12)],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Классы',
        help_text='Если ни один класс не выбран — группа считается «все 1–11».',
    )

    COMPACT_FIELDS = frozenset({'teacher_name'})

    class Meta:
        model = ActivityGroup
        fields = (
            'order',
            'teacher_phone',
            'price',
            'students_status',
            'min_students',
            'max_students',
            'classes',
        ) + _localized(*ACTIVITY_GROUP_TRANSLATABLE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['classes'] = [str(c) for c in (self.instance.classes or [])]
        _apply_backoffice_widget_classes(self, compact_fields=self.COMPACT_FIELDS)
        self.fields['students_status'].widget.attrs['class'] = 'bo-select'
        # Order — hidden; задаётся при создании в `content_activities_group_add`.
        self.fields['order'].widget = forms.HiddenInput()

    def clean_classes(self):
        raw = self.cleaned_data.get('classes') or []
        try:
            values = sorted({int(c) for c in raw if 1 <= int(c) <= 11})
        except (TypeError, ValueError) as exc:
            raise forms.ValidationError('Класс должен быть числом от 1 до 11.') from exc
        return values or list(range(1, 12))

    def clean(self):
        cleaned = super().clean()
        min_s = cleaned.get('min_students')
        max_s = cleaned.get('max_students')
        if min_s is not None and max_s is not None and min_s > max_s:
            raise forms.ValidationError('Минимум учеников не может быть больше максимума.')
        return cleaned


class ScheduleSlotForm(forms.ModelForm):
    class Meta:
        model = ScheduleSlot
        fields = ('order', 'day', 'start_time', 'end_time')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        self.fields['day'].widget.attrs['class'] = 'bo-select'
        for f in ('start_time', 'end_time'):
            self.fields[f].widget.input_type = 'time'
            self.fields[f].widget.attrs['class'] = 'bo-input'


ActivityGroupFormSet = inlineformset_factory(
    parent_model=Activity,
    model=ActivityGroup,
    form=ActivityGroupForm,
    extra=0,
    can_delete=True,
    fk_name='activity',
)

ScheduleSlotFormSet = inlineformset_factory(
    parent_model=ActivityGroup,
    model=ScheduleSlot,
    form=ScheduleSlotForm,
    extra=0,
    can_delete=True,
    fk_name='group',
)
