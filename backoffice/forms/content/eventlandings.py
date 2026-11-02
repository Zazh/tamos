"""EventLanding edit-форма (раздел «Мероприятия») + inline-formset'ы дней,
строк программы, материалов и плиток. Клон EventEditForm: SEO/OG и
переключатель публикации рендерятся ВНЕ основной формы (HTML5 `form=`).

Slug генерируется из title на первом сохранении черновика (см.
views.content.eventlandings). Ведущие — опубликованные участники «Команды»
региона лендинга.
"""

from django import forms
from django.forms import inlineformset_factory

from eventlandings.models import (
    EventLanding,
    EventLandingDay,
    EventLandingMaterial,
    EventLandingProgramRow,
    EventLandingTile,
)
from team.models import TeamMember

from .._common import (
    TRANSLATION_LANGS,
    _apply_backoffice_widget_classes,
    _localized,
    _strip_lang,
    apply_out_of_form_attrs,
    hide_slug_field,
    setup_region_field,
)


EVENTLANDING_TRANSLATABLE = (
    'title',
    'badge_text',
    'lead',
    'audience_title',
    'audience_text',
    'goal',
    'program_title',
    'materials_title',
    'leaders_title',
    'leaders_lead',
    'reg_title',
    'reg_text',
    'form_title',
    'form_lead',
    'form_note',
    'cta_text',
    'price_note',
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)

EVENTLANDING_OUT_OF_FORM_BASES = (
    'seo_title',
    'seo_description',
    'og_title',
    'og_description',
)


class EventLandingEditForm(forms.ModelForm):
    TEXTAREA_ROWS_3 = frozenset({
        'lead', 'audience_text', 'goal', 'leaders_lead', 'reg_text', 'form_lead',
    })
    # CharField, но перенос строки значим (новая строка заголовка на сайте).
    MULTILINE_CHAR_FIELDS = frozenset({'reg_title'})
    OUT_OF_FORM_BASES = frozenset(EVENTLANDING_OUT_OF_FORM_BASES)
    OUT_OF_FORM_FILE_FIELDS = frozenset({'is_published'})
    FORM_ID = 'eventlanding-edit-form'

    leaders = forms.ModelMultipleChoiceField(
        queryset=TeamMember.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Ведущие',
    )

    class Meta:
        model = EventLanding
        fields = (
            'region',
            'slug',
            'is_published',
            'is_paid',
            'price',
            'show_parent_checkbox',
            'leaders',
        ) + _localized(*EVENTLANDING_TRANSLATABLE)
        widgets = {
            'is_published': forms.CheckboxInput(),
            'is_paid': forms.CheckboxInput(),
            'show_parent_checkbox': forms.CheckboxInput(),
            'price': forms.NumberInput(attrs={'min': 0, 'step': 1}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            base = _strip_lang(name)
            if base in self.MULTILINE_CHAR_FIELDS:
                field.widget = forms.Textarea(attrs={'rows': 2})
            elif base in self.TEXTAREA_ROWS_3:
                field.widget.attrs['rows'] = 3

        _apply_backoffice_widget_classes(self)

        hide_slug_field(self)

        apply_out_of_form_attrs(
            self, self.FORM_ID, self.OUT_OF_FORM_BASES, self.OUT_OF_FORM_FILE_FIELDS,
        )

        instance = kwargs.get('instance')
        setup_region_field(self, user=user, instance=instance)

        # Ведущие — только опубликованные участники «Команды» региона лендинга:
        # pk чужого региона из POST → ошибка «выберите корректный вариант».
        region_id = instance.region_id if instance else None
        self.fields['leaders'].queryset = (
            TeamMember.objects.filter(region_id=region_id, is_published=True)
            .order_by('order', 'pk')
        )
        self.fields['leaders'].widget.attrs['class'] = 'bo-role-card-input'

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('is_published') and not (cleaned.get('title_ru') or '').strip():
            raise forms.ValidationError(
                'Чтобы опубликовать мероприятие, заполните заголовок на русском.'
            )
        if cleaned.get('is_paid'):
            if cleaned.get('price') is None:
                self.add_error('price', 'Укажите цену платного мероприятия (₸, целое).')
        else:
            # Чекбокс «родитель ученика» живёт только у платных — скрытый в UI
            # флаг не должен включать его на сайте у бесплатного события.
            cleaned['show_parent_checkbox'] = False
        return cleaned


# ----- Inline: дни, программа дня, материалы, плитки ------------------------

# `type=date`/`type=time` ждут ISO-значение независимо от локали (USE_L10N).
def _date_input():
    return forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


def _time_input():
    return forms.TimeInput(attrs={'type': 'time'}, format='%H:%M')


def _require_ru(form, *bases):
    """Строка inline без русского заголовка не сохраняется: на сайте она пустая."""
    for base in bases:
        form.fields[f'{base}_ru'].required = True


class EventLandingDayForm(forms.ModelForm):
    class Meta:
        model = EventLandingDay
        fields = ('date', 'start', 'end') + _localized('label')
        widgets = {'date': _date_input(), 'start': _time_input(), 'end': _time_input()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('start'), cleaned.get('end')
        if start and end and end <= start:
            self.add_error('end', 'Окончание должно быть позже начала.')
        return cleaned


EventLandingDayFormSet = inlineformset_factory(
    parent_model=EventLanding,
    model=EventLandingDay,
    form=EventLandingDayForm,
    extra=0,
    can_delete=True,
)


class EventLandingProgramRowForm(forms.ModelForm):
    class Meta:
        model = EventLandingProgramRow
        fields = ('order', 'start', 'duration_min', 'is_break') + _localized('title', 'text')
        widgets = {
            'order': forms.HiddenInput(),
            'start': _time_input(),
            'duration_min': forms.NumberInput(attrs={'min': 1, 'step': 5}),
            'is_break': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        _require_ru(self, 'title')


EventLandingProgramRowFormSet = inlineformset_factory(
    parent_model=EventLandingDay,
    model=EventLandingProgramRow,
    form=EventLandingProgramRowForm,
    extra=0,
    can_delete=True,
)


class EventLandingMaterialForm(forms.ModelForm):
    class Meta:
        model = EventLandingMaterial
        fields = ('order',) + _localized('title')
        widgets = {'order': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        _require_ru(self, 'title')


EventLandingMaterialFormSet = inlineformset_factory(
    parent_model=EventLanding,
    model=EventLandingMaterial,
    form=EventLandingMaterialForm,
    extra=0,
    can_delete=True,
)


class EventLandingTileForm(forms.ModelForm):
    class Meta:
        model = EventLandingTile
        fields = ('order',) + _localized('title', 'text')
        # text — CharField(200), но в UI это 1–2 строки описания.
        widgets = {
            'order': forms.HiddenInput(),
            **{f'text_{lang}': forms.Textarea(attrs={'rows': 2}) for lang in TRANSLATION_LANGS},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_backoffice_widget_classes(self)
        _require_ru(self, 'title')


EventLandingTileFormSet = inlineformset_factory(
    parent_model=EventLanding,
    model=EventLandingTile,
    form=EventLandingTileForm,
    extra=0,
    can_delete=True,
)
